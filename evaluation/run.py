"""Save one complete generation trace per verified question; never auto-score candidates."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from evaluation.dataset import read_dataset

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--no-reranker', action='store_true')
    parser.add_argument('--top-k', type=int, default=10)
    parser.add_argument('--final-k', type=int, default=3)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    rows = read_dataset(args.dataset, verified_only=True)
    if args.limit:
        rows = rows[:args.limit]
    from rag_pipeline import generate
    from vector_store import get_collection
    collection = get_collection()
    ids = sorted(collection.get(include=[])['ids'])
    corpus_hash = hashlib.sha256('\n'.join(ids).encode()).hexdigest()
    dataset_hash = hashlib.sha256(Path(args.dataset).read_bytes()).hexdigest()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation: preserve previous experiments.
    with output.open('x', encoding='utf-8') as handle:
        for row in rows:
            result = dict(question_id=row['id'], question=row['question'], category=row['category'],
                          answerable=row['answerable'], reference=row.get('reference_answer', ''),
                          required_claims=row.get('required_claims', []), evidence=row.get('evidence', []),
                          dataset_sha256=dataset_hash, index_contents_sha256=corpus_hash,
                          created_at=datetime.now(timezone.utc).isoformat())
            try:
                result.update(generate(dict(question=row['question'], history=row.get('history', []),
                                            top_k=args.top_k, final_k=args.final_k,
                                            use_reranker=not args.no_reranker)))
                result['status'] = 'ok'
            except Exception as exc:
                result.update(status='error', error_type=type(exc).__name__)
            handle.write(json.dumps(result, ensure_ascii=False) + '\n')
            handle.flush()
            print(row['id'], result['status'])
    if hashlib.sha256('\n'.join(sorted(collection.get(include=[])['ids'])).encode()).hexdigest() != corpus_hash:
        raise RuntimeError('Index changed during evaluation; invalidate this run')

if __name__ == '__main__':
    main()
