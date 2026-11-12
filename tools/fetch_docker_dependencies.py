"""Fetch only template dependencies referenced by the pinned Docker selection."""
import hashlib
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen
ROOT = Path(__file__).resolve().parents[1] / 'data/docker_official'
def fetch(url):
    with urlopen(Request(url, headers={'User-Agent': 'RAG-corpus-preparation'}), timeout=60) as r:
        return r.read()
def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    revision = manifest['commit']
    tree = json.loads(fetch(f'https://api.github.com/repos/docker/docs/git/trees/{revision}?recursive=1'))
    paths = {x['path'] for x in tree['tree'] if x['type'] == 'blob'}
    if tree.get('truncated'):
        raise RuntimeError('Truncated source tree')
    needed = set()
    for item in manifest['documents']:
        text = (ROOT / item['local_path']).read_text(encoding='utf-8-sig')
        for name in re.findall(r'\{\{%\s*include\s+"([^"]+)"', text):
            matches = [p for p in paths if p.endswith('/' + name) and ('includes/' in p or '_includes/' in p)]
            if len(matches) != 1:
                raise RuntimeError(f'Ambiguous include {name}: {matches}')
            needed.add(matches[0])
    needed.update(p for p in paths if p.startswith('data/') and 'feature' in p.lower() and '/cli/' not in p)
    needed.update(p for p in paths if 'summary-bar' in p)
    needed.update(p for p in paths if p.startswith('data/summary'))
    needed.update(p for p in paths if p in {'hugo.yaml', 'hugo.yml', 'hugo.toml'})
    records = []
    for path in sorted(needed):
        data = fetch(f'https://raw.githubusercontent.com/docker/docs/{revision}/{path}')
        target = ROOT / 'dependencies' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        records.append(dict(repository_path=path, local_path=target.relative_to(ROOT).as_posix(),
                            source_url=f'https://github.com/docker/docs/blob/{revision}/{path}',
                            sha256=hashlib.sha256(data).hexdigest()))
    (ROOT / 'dependencies.json').write_text(json.dumps(dict(commit=revision, files=records), indent=2), encoding='utf-8')
    print(json.dumps([r['repository_path'] for r in records], indent=2))
if __name__ == '__main__':
    main()
