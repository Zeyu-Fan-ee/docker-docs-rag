"""Prepare source artifacts or build a fresh, versioned Chroma collection."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from document_processor import load_corpus
from ingestion import chunk_documents, chunk_records, index_spec, index_fingerprint, write_vectors
from project_config import ARTIFACT_DIR, CORPUS_DIR, COLLECTION_NAME, DB_PATH


def prepare():
    docs = load_corpus()
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with (ARTIFACT_DIR / 'parsed_sections.jsonl').open('w', encoding='utf-8') as f:
        for d in docs:
            f.write(json.dumps(dict(text=d.page_content, metadata=d.metadata), ensure_ascii=False) + '\n')
    manifest = json.loads((CORPUS_DIR / 'manifest.json').read_text(encoding='utf-8'))
    warnings = {}
    for doc in docs:
        issues = json.loads(doc.metadata.get('parser_warnings', '[]'))
        if issues:
            warnings[doc.metadata['source']] = issues
    included = {d.metadata.get('repository_path') for d in docs}
    primary = {d['repository_path'] for d in manifest['documents']}
    excluded = [dict(path=d['repository_path'], reason='navigation-only page without body text')
                for d in manifest['documents'] if d['repository_path'] not in included]
    report = dict(status='parsed_not_indexed', source_files=len(manifest['documents']),
                  included_files=len(included & primary), supporting_files=len(included - primary), excluded_files=excluded,
                  corpus_revision=manifest['commit'], sections=len(docs),
                  characters=sum(len(d.page_content) for d in docs),
                  template_warnings=warnings, index_spec=index_spec())
    (ARTIFACT_DIR / 'preparation_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return docs, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-only', action='store_true', help='Parse/check all sources, no model or DB')
    args = parser.parse_args()
    docs, report = prepare()
    print(f'Parsed {len(docs)} sections from {report["included_files"]} documents and {report["supporting_files"]} supporting files', flush=True)
    if args.prepare_only:
        print(json.dumps({k: v for k, v in report.items() if k not in ('index_spec', 'template_warnings')}, indent=2))
        print('Files requiring template review:', len(report['template_warnings']))
        return
    if report['template_warnings']:
        raise RuntimeError('Unresolved source templates: review preparation_report.json before building.')
    from vector_store import get_client
    client = get_client()
    names = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in names:
        raise RuntimeError('Collection already exists. Choose a new COLLECTION_NAME for a fresh build; no overwrite is performed.')
    print('Starting chunking and tokenizer length checks...', flush=True)
    records = chunk_records(chunk_documents(docs))
    if not records:
        raise RuntimeError('No chunks generated')
    with (ARTIFACT_DIR / 'chunks.jsonl').open('w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    collection = client.create_collection(COLLECTION_NAME, embedding_function=None,
        configuration={'hnsw': {'space': 'cosine'}},
        metadata={'status': 'building', 'index_fingerprint': index_fingerprint(),
                  'corpus_revision': report['corpus_revision']})
    try:
        write_vectors(collection, records)
        collection.modify(metadata=dict(collection.metadata, status='ready'))
    except Exception:
        collection.modify(metadata=dict(collection.metadata, status='failed'))
        raise
    report.update(status='indexed', chunks=len(records), database=DB_PATH, collection=COLLECTION_NAME,
                  index_fingerprint=index_fingerprint(), completed_at=datetime.now(timezone.utc).isoformat())
    (ARTIFACT_DIR / 'build_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Indexed {len(records)} chunks into {COLLECTION_NAME}')


if __name__ == '__main__':
    main()
