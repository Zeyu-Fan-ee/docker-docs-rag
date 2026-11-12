"""Configuration only: no model loading or DB access at import time."""
import os
from pathlib import Path
from dotenv import load_dotenv
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / '.env')
def project_path(name, default):
    p = Path(os.getenv(name, default))
    return p if p.is_absolute() else PROJECT_ROOT / p
CORPUS_DIR = project_path('CORPUS_DIR', 'data/docker_official')
DB_PATH = str(project_path('DB_PATH', 'chroma_db_docker'))
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'docker_documentation')
UPLOAD_DIR = project_path('UPLOAD_DIR', 'data/uploads')
ARTIFACT_DIR = project_path('ARTIFACT_DIR', 'artifacts')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'BAAI/bge-m3')
RERANKER_MODEL = os.getenv('RERANKER_MODEL', 'BAAI/bge-reranker-v2-m3')
MODEL_DEVICE = os.getenv('MODEL_DEVICE', 'cpu')
EMBEDDING_MAX_LENGTH = int(os.getenv('EMBEDDING_MAX_LENGTH', '512'))
CHUNK_METHOD = os.getenv('CHUNK_METHOD', 'semantic')
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '650'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '100'))
TOP_K = int(os.getenv('TOP_K', '10'))
FINAL_K = int(os.getenv('FINAL_K', '3'))
USE_RERANKER = os.getenv('USE_RERANKER', 'true').lower() == 'true'
MAX_SIZE = 10 * 1024 * 1024
PARSER_VERSION = 'docker-markdown-v1'
PROMPT_VERSION = 'docker-grounded-v1'
if CHUNK_METHOD not in {'semantic', 'recursive'}:
    raise ValueError('CHUNK_METHOD must be semantic or recursive')
if not 0 <= CHUNK_OVERLAP < CHUNK_SIZE or min(TOP_K, FINAL_K, EMBEDDING_MAX_LENGTH) < 1:
    raise ValueError('Invalid chunk/retrieval configuration')
def experiment_config():
    return dict(embedding_model=EMBEDDING_MODEL, embedding_max_length=EMBEDDING_MAX_LENGTH,
                chunk_method=CHUNK_METHOD, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
                parser_version=PARSER_VERSION, top_k=TOP_K, final_k=FINAL_K,
                use_reranker=USE_RERANKER, reranker_model=RERANKER_MODEL,
                model_device=MODEL_DEVICE, prompt_version=PROMPT_VERSION,
                generation_model=os.getenv('MODEL_ID', ''), collection=COLLECTION_NAME)
