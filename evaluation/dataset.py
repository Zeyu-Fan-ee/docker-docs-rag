import json
from pathlib import Path

def read_dataset(path, verified_only=False):
    rows = [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]
    if not rows:
        raise ValueError('Dataset is empty')
    seen = set()
    for row in rows:
        for key in ('id', 'question', 'category', 'answerable', 'verification_status', 'split'):
            if key not in row:
                raise ValueError(f'Missing dataset field: {key}')
        if row['id'] in seen or not row['question'].strip() or not isinstance(row['answerable'], bool):
            raise ValueError('Invalid or duplicate question')
        seen.add(row['id'])
        if row['verification_status'] == 'verified' and row['answerable']:
            if not row.get('reference_answer') or not row.get('evidence') or not row.get('required_claims'):
                raise ValueError(f"Verified question lacks answer/evidence: {row['id']}")
    if verified_only:
        rows = [r for r in rows if r['verification_status'] == 'verified']
        if not rows:
            raise ValueError('No verified questions; review candidates before evaluation')
    return rows
