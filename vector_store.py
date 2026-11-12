"""Lazy Chroma access and compatibility checks."""
from pathlib import Path
from functools import lru_cache
from project_config import DB_PATH, COLLECTION_NAME
from ingestion import index_fingerprint

class IndexNotReady(RuntimeError):
    pass

@lru_cache(maxsize=1)
def get_client():
    import chromadb
    return chromadb.PersistentClient(path=DB_PATH)

def get_collection():
    if not (Path(DB_PATH) / 'chroma.sqlite3').exists():
        raise IndexNotReady('Docker index not built. Run python build_db.py first.')
    try:
        collection = get_client().get_collection(COLLECTION_NAME, embedding_function=None)
    except Exception as exc:
        raise IndexNotReady(f'Collection {COLLECTION_NAME} is unavailable. Build the index first.') from exc
    meta = collection.metadata or {}
    if meta.get('status') != 'ready' or not collection.count():
        raise IndexNotReady('Index is empty, incomplete, or failed. Build a new collection.')
    if meta.get('index_fingerprint') != index_fingerprint():
        raise IndexNotReady('Index configuration differs from current processing settings. Build a new collection.')
    return collection
