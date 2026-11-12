"""Replay saved baseline contexts with adjacent chunks; never alter the baseline."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import project_config
from rag_pipeline import get_llm, messages, source_location


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--chunks', default='artifacts/chunks.jsonl')
    parser.add_argument('--output', required=True)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    baseline_path, chunks_path, output = map(Path, (args.input, args.chunks, args.output))
    rows, chunks = read_jsonl(baseline_path), read_jsonl(chunks_path)
    by_id = {c['id']: c for c in chunks}
    by_position = {(c['metadata']['document_id'], c['metadata']['section'], c['metadata']['chunk_index']): c for c in chunks}
    if len(by_id) != len(chunks) or len(by_position) != len(chunks):
        raise ValueError('Duplicate chunk IDs or positions')
    if os.getenv('MODEL_ID') != 'deepseek-flash':
        raise ValueError('Replay requires the original deepseek-flash generation model')
    for row in rows:
        if row['status'] != 'ok' or row['config']['generation_model'] != os.getenv('MODEL_ID'):
            raise ValueError('Baseline has a failed row or different generation model')
        if row['prompt_version'] != project_config.PROMPT_VERSION:
            raise ValueError('Prompt version differs from baseline')
        for item in row['retrieval_trace']['selected']:
            if item['chunk_id'] not in by_id or by_id[item['chunk_id']]['text'] != item['text']:
                raise ValueError('Saved selected chunk differs from local chunks')
    baseline_sha = hashlib.sha256(baseline_path.read_bytes()).hexdigest()
    chunks_sha = hashlib.sha256(chunks_path.read_bytes()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as handle:
        for row in rows[:args.limit] if args.limit else rows:
            selected = row['retrieval_trace']['selected']
            ordered = [(item['chunk_id'], item['text'], item['metadata'], 'baseline') for item in selected]
            seen = {item[0] for item in ordered}
            for item in selected:
                m = item['metadata']
                for offset in (-1, 1):
                    neighbor = by_position.get((m['document_id'], m['section'], m['chunk_index'] + offset))
                    if neighbor and neighbor['id'] not in seen:
                        ordered.append((neighbor['id'], neighbor['text'], neighbor['metadata'], 'neighbor'))
                        seen.add(neighbor['id'])
            contexts = [x[1] for x in ordered]
            sources = [dict(citation=f'[{i}]', source=meta['source'], chunk_id=cid,
                            location=source_location(meta), role=role)
                       for i, (cid, _, meta, role) in enumerate(ordered, 1)]
            prepared = dict(question=row['question'], history=row.get('history', ''),
                            context='\n\n'.join(f'[{i}] {text}' for i, text in enumerate(contexts, 1)))
            result = dict(question_id=row['question_id'], question=row['question'], category=row['category'],
                          answerable=row['answerable'], reference=row['reference'], required_claims=row['required_claims'],
                          evidence=row['evidence'], retrieved_contexts=contexts, sources=sources,
                          baseline_input_sha256=baseline_sha, chunks_sha256=chunks_sha,
                          baseline_dataset_sha256=row['dataset_sha256'], baseline_index_sha256=row['index_contents_sha256'],
                          config=row['config'], prompt_version=project_config.PROMPT_VERSION,
                          strategy='saved_top3_plus_same_section_previous_next', created_at=datetime.now(timezone.utc).isoformat())
            try:
                response = get_llm().invoke(messages(prepared))
                result.update(answer=response.content, usage=response.usage_metadata or {}, status='ok')
            except Exception as exc:
                result.update(answer='', status='error', error_type=type(exc).__name__)
            handle.write(json.dumps(result, ensure_ascii=False) + '\n')
            handle.flush()
            print(row['question_id'], result['status'], 'contexts', len(contexts), flush=True)


if __name__ == '__main__':
    main()
