"""Shared chunking/ID/index contracts for offline builds and uploads."""
import hashlib
import json
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from project_config import (CHUNK_METHOD, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL,
                            EMBEDDING_MAX_LENGTH, PARSER_VERSION, PROJECT_ROOT)

def index_spec():
    # Include processing implementation hashes so edits cannot silently reuse stale vectors.
    hashes = {n: hashlib.sha256((PROJECT_ROOT / n).read_bytes()).hexdigest()
              for n in ('document_processor.py', 'semantic_chunker.py', 'ingestion.py', 'embedding_model.py')}
    from project_config import CORPUS_DIR
    dependencies = CORPUS_DIR / 'dependencies.json'
    dependency_hash = hashlib.sha256(dependencies.read_bytes()).hexdigest() if dependencies.exists() else ''
    return dict(embedding_model=EMBEDDING_MODEL, max_length=EMBEDDING_MAX_LENGTH,
                method=CHUNK_METHOD, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP,
                parser=PARSER_VERSION, dependency_manifest=dependency_hash, implementation=hashes)

def index_fingerprint():
    return hashlib.sha256(json.dumps(index_spec(), sort_keys=True).encode()).hexdigest()

def chunk_documents(documents, token_guard=True):
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    if CHUNK_METHOD == 'semantic':
        from semantic_chunker import semantic_split
        chunks = []
        for i, doc in enumerate(documents, 1):
            chunks.extend(semantic_split(
                doc, min_chars=max(1, CHUNK_SIZE // 2), target_chars=CHUNK_SIZE,
                max_chars=max(CHUNK_SIZE + 1, int(CHUNK_SIZE * 1.4)), overlap_chars=CHUNK_OVERLAP))
            if i == 1 or i % 25 == 0 or i == len(documents):
                print(f'Semantic chunking: {i}/{len(documents)} sections; {len(chunks)} chunks', flush=True)
    else:
        chunks = splitter.split_documents(documents)
    if token_guard:
        from embedding_model import get_embedding_model
        tokenizer = get_embedding_model().tokenizer
        budget = EMBEDDING_MAX_LENGTH - tokenizer.num_special_tokens_to_add(pair=False)
        # Ensure even pathological Unicode/code lines fit the tokenizer limit exactly.
        guarded = []
        def fit(text, meta):
            if len(tokenizer.encode(text, add_special_tokens=False)) <= budget:
                guarded.append(Document(page_content=text, metadata=meta.copy()))
            elif len(text) > 1:
                middle = len(text) // 2
                fit(text[:middle], meta)
                fit(text[middle:], meta)
            else:
                raise ValueError('Token limit too small for a character')
        for chunk in chunks:
            fit(chunk.page_content, chunk.metadata)
        chunks = guarded
    return [c for c in chunks if c.page_content.strip()]

def chunk_records(chunks):
    counters, records = {}, []
    for chunk in chunks:
        meta = {k: v for k, v in chunk.metadata.items() if v is not None}
        doc_id = meta['document_id']
        i = counters.get(doc_id, 0)
        counters[doc_id] = i + 1
        key = f'{doc_id}:{index_fingerprint()}:{i}:{chunk.page_content}'
        chunk_id = hashlib.sha256(key.encode()).hexdigest()
        meta.update(chunk_id=chunk_id, chunk_index=i)
        records.append(dict(id=chunk_id, text=chunk.page_content, metadata=meta))
    return records

def write_vectors(collection, records):
    from embedding_model import encode_texts
    for start in range(0, len(records), 32):
        batch = records[start:start + 32]
        embeddings = encode_texts([r['text'] for r in batch])
        collection.upsert(ids=[r['id'] for r in batch], documents=[r['text'] for r in batch],
                          metadatas=[r['metadata'] for r in batch], embeddings=embeddings.tolist())
        print(f'Indexed vectors: {min(start + 32, len(records))}/{len(records)}', flush=True)
