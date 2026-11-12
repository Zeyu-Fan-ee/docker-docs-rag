
import os
import json
import uuid

import requests
import streamlit as st


API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(
    page_title="Docker RAG Assistant",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Docker Knowledge Base Assistant")
st.caption("BGE-M3 + ChromaDB + BGE Reranker + LangChain")


# 初始化会话
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []


# 侧边栏
with st.sidebar:
    st.header("Settings")

    if st.button("New Conversation"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    st.write("Session ID:")
    st.code(st.session_state.session_id)

    try:
        response = requests.get(
            f"{API_URL}/ready",
            timeout=5
        )
        response.raise_for_status()
        st.success("API Connected")
    except requests.RequestException:
        st.warning("知识库尚未就绪：请启动后端并完成建库。")

    st.info("依据所选 Docker 官方文档回答；资料范围以当前知识库为准。")
    uploaded = st.file_uploader("添加文档（会改变当前知识库，正式评测期间请勿上传）", type=["md", "txt", "pdf", "docx"])
    if uploaded is not None and st.button("上传并入库"):
        try:
            with st.spinner("解析与入库中…"):
                response = requests.post(f"{API_URL}/upload", files={"file": (uploaded.name, uploaded.getvalue())}, timeout=600)
                response.raise_for_status()
                st.success(response.json())
        except requests.RequestException as exc:
            st.error(f"上传失败: {exc}")


# 来源展示
def show_sources(sources):
    if not sources:
        return

    with st.expander("📄 Document Sources"):
        for source in sources:
            label = source['source']
            if label.startswith("https://github.com/docker/docs/blob/"):
                label = f"[官方文档]({label})"
            st.markdown(f"**{source['citation']}** {label} — {source.get('location', 'Location unavailable')}")
            st.caption(
                f"Chunk ID: {source['chunk_id']}"
            )


# 读取 SSE
def stream_answer(question, session_id, result):
    payload = {
        "session_id": session_id,
        "question": question
    }

    with requests.post(
        f"{API_URL}/chat/stream",
        json=payload,
        stream=True,
        timeout=(10, 600)
    ) as response:

        response.raise_for_status()

        completed = False

        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue

            if isinstance(line, bytes):
                line = line.decode("utf-8")

            if not line.startswith("data: "):
                continue

            event = json.loads(line[6:])

            if event["type"] == "metadata":
                result["search_query"] = event["search_query"]

            elif event["type"] == "token":
                yield event["content"]

            elif event["type"] == "done":
                result["sources"] = event["sources"]
                completed = True

            elif event["type"] == "error":
                raise RuntimeError(event["content"])

        if not completed:
            raise RuntimeError("Streaming ended before completion.")


# 展示已有消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            show_sources(message.get("sources", []))


# 用户输入
question = st.chat_input("Ask a question about Docker networking, storage, or Compose...")

if question:
    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        result = {
            "sources": [],
            "search_query": ""
        }

        try:
            answer = st.write_stream(
                stream_answer(
                    question,
                    st.session_state.session_id,
                    result
                )
            )

            show_sources(result["sources"])

            with st.expander("🔎 Retrieval Details"):
                st.write("Search Query:", result["search_query"])

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": result["sources"]
            })

        except Exception as e:
            st.error(f"Request failed: {e}")
