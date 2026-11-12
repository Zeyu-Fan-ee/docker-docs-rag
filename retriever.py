from functools import lru_cache
from time import perf_counter
from embedding_model import encode_texts
from project_config import TOP_K, FINAL_K, USE_RERANKER, RERANKER_MODEL, MODEL_DEVICE
from vector_store import get_collection

@lru_cache(maxsize=1)
def get_reranker():
    from FlagEmbedding import FlagReranker
    return FlagReranker(RERANKER_MODEL, use_fp16=False, devices=MODEL_DEVICE)

def retrieve(question, top_k=TOP_K):
    if top_k < 1:
        raise ValueError('top_k must be positive')
    collection = get_collection()
    embedding = encode_texts([question])[0]
    return collection.query(query_embeddings=[embedding.tolist()], n_results=min(top_k, collection.count()),
                            include=['documents', 'metadatas', 'distances'])

def retrieve_trace(question, top_k=TOP_K, final_k=FINAL_K, use_reranker=USE_RERANKER):
    if final_k < 1 or final_k > top_k:
        raise ValueError('Require 1 <= final_k <= top_k')
    start = perf_counter()
    result = retrieve(question, top_k)
    candidates = [dict(text=text, metadata=meta or {}, chunk_id=chunk_id,
                       distance=float(distance), original_rank=i + 1, rerank_score=None)
                  for i, (text, meta, chunk_id, distance) in enumerate(zip(
                      result['documents'][0], result['metadatas'][0], result['ids'][0], result['distances'][0]))]
    retrieved_at = perf_counter()
    ranked = [dict(c) for c in candidates]
    if use_reranker and ranked:
        scores = get_reranker().compute_score([[question, c['text']] for c in ranked], batch_size=2)
        if not hasattr(scores, '__len__'):
            scores = [scores]
        for c, score in zip(ranked, scores):
            c['rerank_score'] = float(score)
        ranked.sort(key=lambda c: c['rerank_score'], reverse=True)
    return dict(candidates=candidates, ranked=ranked, selected=ranked[:final_k],
                timings={'retrieval_seconds': retrieved_at-start, 'rerank_seconds': perf_counter()-retrieved_at})

def retrieve_reranked(question, top_k=TOP_K, final_k=FINAL_K):
    return retrieve_trace(question, top_k, final_k)['selected']
