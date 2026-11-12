"""Print presence/status only; never expose credential values or call a model."""
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from project_config import ARTIFACT_DIR, DB_PATH, COLLECTION_NAME

def main():
    from importlib.metadata import version, PackageNotFoundError
    dependencies = {}
    for name in ('chromadb', 'FlagEmbedding', 'fastapi', 'streamlit', 'ragas'):
        try:
            dependencies[name] = version(name)
        except PackageNotFoundError:
            dependencies[name] = None
    cache = Path(os.getenv('HF_HOME', str(Path.home() / '.cache/huggingface'))) / 'hub'
    report = dict(python=sys.version.split()[0], dependencies=dependencies,
                  llm_settings_present={n: bool(os.getenv(n)) for n in ('MODEL_ID', 'API_KEY', 'BASE_URL')},
                  judge_settings_present={n: bool(os.getenv(n)) for n in ('JUDGE_MODEL_ID', 'JUDGE_API_KEY', 'JUDGE_BASE_URL')},
                  embedding_weights_present=any((cache / 'models--BAAI--bge-m3' / 'snapshots').glob('**/pytorch_model.bin')) or any((cache / 'models--BAAI--bge-m3' / 'snapshots').glob('**/*.safetensors')),
                  reranker_weights_present=any((cache / 'models--BAAI--bge-reranker-v2-m3' / 'snapshots').glob('**/pytorch_model.bin')) or any((cache / 'models--BAAI--bge-reranker-v2-m3' / 'snapshots').glob('**/*.safetensors')),
                  docker_installed=shutil.which('docker') is not None,
                  database_exists=(Path(DB_PATH) / 'chroma.sqlite3').exists(), collection=COLLECTION_NAME)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_DIR / 'environment_check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
if __name__ == '__main__':
    main()
