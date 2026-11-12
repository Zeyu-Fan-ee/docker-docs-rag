import hashlib
import re
from pathlib import Path
from threading import Lock
from document_processor import load_document, SUPPORTED_SUFFIXES
from ingestion import chunk_documents, chunk_records, write_vectors
from project_config import UPLOAD_DIR, MAX_SIZE
from vector_store import get_collection
upload_lock = Lock()

def upload_and_index(filename, content):
    safe_name = Path(filename.replace('\\', '/')).name
    if not safe_name or safe_name != filename or safe_name.startswith('.') or re.search(r'[<>:"/\\|?*]', safe_name):
        raise ValueError('Invalid filename')
    if Path(safe_name).suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError('Supported formats: MD, TXT, PDF, DOCX')
    if not content or len(content) > MAX_SIZE:
        raise ValueError('File must be nonempty and no larger than 10 MiB')
    digest = hashlib.sha256(content).hexdigest()
    with upload_lock:
        collection = get_collection()
        if collection.get(where={'file_sha256': digest}, limit=1)['ids']:
            return dict(status='duplicate', filename=safe_name, total_chunks=collection.count())
        target = UPLOAD_DIR / safe_name
        if target.exists() or collection.get(where={'filename': safe_name}, limit=1)['ids']:
            raise ValueError('Filename already exists; choose a unique name')
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        try:
            documents = load_document(target)
            if not documents:
                raise ValueError('No extractable text')
            if any(d.metadata.get('parser_warnings', '[]') != '[]' for d in documents):
                raise ValueError('Unresolved Markdown templates require preprocessing')
            records = chunk_records(chunk_documents(documents))
            if not records:
                raise ValueError('No chunks generated')
            write_vectors(collection, records)
            return dict(status='indexed', filename=safe_name, document_id=digest,
                        chunks_added=len(records), total_chunks=collection.count())
        except Exception:
            try:
                collection.delete(where={'file_sha256': digest})
            finally:
                target.unlink(missing_ok=True)
            raise
