from fastapi import UploadFile, File
from upload_service import upload_and_index, MAX_SIZE
from vector_store import IndexNotReady, get_collection
from project_config import COLLECTION_NAME

import json
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from rag_pipeline import rag_chain, stream_rag


app = FastAPI(title="Docker Knowledge Base RAG API")

# 按 session_id 保存历史
sessions = {}
session_lock = Lock()


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    question: str = Field(min_length=1)


def get_history(session_id):
    with session_lock:
        return sessions.get(session_id, []).copy()


def save_history(session_id, question, answer):
    with session_lock:
        sessions.setdefault(session_id, []).extend([
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer}
        ])
        sessions[session_id] = sessions[session_id][-6:]


@app.get("/health")
def health():
    return {"status": "ok", "service": "docker-rag"}


@app.get("/ready")
def readiness():
    try:
        collection = get_collection()
        return {"status": "ready", "collection": COLLECTION_NAME, "chunks": collection.count()}
    except IndexNotReady as exc:
        raise HTTPException(503, str(exc))


# 1. 普通问答
@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(400, "Question cannot be empty")

    history = get_history(request.session_id)

    try:
        result = rag_chain.invoke({
            "question": question,
            "history": history
        })

        save_history(
            request.session_id,
            question,
            result["answer"]
        )

        return {
            "session_id": request.session_id,
            "question": question,
            "search_query": result["search_query"],
            "answer": result["answer"],
            "sources": result["sources"]
        }

    except IndexNotReady as e:
        raise HTTPException(503, str(e))

    except Exception as e:
        print("Chat error:", repr(e))
        raise HTTPException(500, "RAG request failed")


# 2. SSE 流式问答
@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    try:
        get_collection()
    except IndexNotReady as exc:
        raise HTTPException(503, str(exc))
    question = request.question.strip()

    if not question:
        raise HTTPException(400, "Question cannot be empty")

    history = get_history(request.session_id)

    def event_generator():
        try:
            for event in stream_rag({
                "question": question,
                "history": history
            }):

                if event["type"] == "done":
                    save_history(
                        request.session_id,
                        question,
                        event["answer"]
                    )

                yield (
                    "data: "
                    + json.dumps(event, ensure_ascii=False)
                    + "\n\n"
                )

        except Exception as e:
            print("Stream error:", repr(e))

            error_event = {
                "type": "error",
                "content": "RAG streaming failed"
            }

            yield (
                "data: "
                + json.dumps(error_event)
                + "\n\n"
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )



@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        content = await file.read(MAX_SIZE + 1)

        result = upload_and_index(
            filename=file.filename or "",
            content=content
        )

        return result

    except IndexNotReady as e:
        raise HTTPException(503, str(e))

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        print("Upload error:", repr(e))
        raise HTTPException(
            status_code=500,
            detail="Document indexing failed"
        )

    finally:
        await file.close()
