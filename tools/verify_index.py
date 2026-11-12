"""Validate an existing index and run real retrieval smoke checks; no LLM calls."""
import argparse
import json
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_config import ARTIFACT_DIR, EMBEDDING_MAX_LENGTH

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rerank', action='store_true', help='Also load the real reranker')
    args = parser.parse_args()
    from vector_store import get_collection
    from ingestion import index_fingerprint
    from embedding_model import get_embedding_model
    from retriever import retrieve_trace
    collection = get_collection()
    build = json.loads((ARTIFACT_DIR / 'build_report.json').read_text(encoding='utf-8'))
    records = [json.loads(line) for line in (ARTIFACT_DIR / 'chunks.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    if collection.count() != len(records) or collection.count() != build['chunks']:
        raise RuntimeError('Record count differs from build artifacts')
    if len({r['id'] for r in records}) != len(records):
        raise RuntimeError('Duplicate chunk IDs')
    stored_ids = set(collection.get(include=[])['ids'])
    if stored_ids != {r['id'] for r in records}:
        raise RuntimeError('Stored IDs differ from build artifacts')
    sample = collection.get(limit=1, include=['embeddings'])['embeddings'][0]
    if len(sample) != 1024 or not all(math.isfinite(float(x)) for x in sample):
        raise RuntimeError('Invalid embedding sample')
    model = get_embedding_model()
    tokenizer = model.tokenizer
    lengths = [len(tokenizer.encode(r['text'], add_special_tokens=True)) for r in records]
    if max(lengths) > EMBEDDING_MAX_LENGTH:
        raise RuntimeError('Chunks exceed embedding token budget')
    checks = []
    questions = ['Does deleting a container remove data stored in Docker volumes?',
                 'Docker 的用户自定义 bridge 网络和默认 bridge 网络有什么区别？',
                 'How do I control startup order in Docker Compose?']
    for question in questions:
        print('Checking:', question, flush=True)
        trace = retrieve_trace(question, top_k=10, final_k=3, use_reranker=args.rerank)
        checks.append(dict(question=question, timings=trace['timings'], results=[dict(
            chunk_id=r['chunk_id'], source=r['metadata']['source'],
            section=r['metadata'].get('section'), distance=r['distance'],
            rerank_score=r['rerank_score']) for r in trace['selected']]))
    report = dict(status='passed', collection=collection.name, chunks=collection.count(),
                  embedding_dimension=len(sample), max_chunk_tokens=max(lengths),
                  index_fingerprint=index_fingerprint(), reranker_used=args.rerank,
                  quality_evaluation=False, retrieval_smoke_checks=checks)
    name = 'index_verification_reranked.json' if args.rerank else 'index_verification_dense.json'
    (ARTIFACT_DIR / name).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)

if __name__ == '__main__':
    main()
