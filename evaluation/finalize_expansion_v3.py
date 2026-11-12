"""Apply approved claim-review changes to a new, reviewable dataset version."""
import hashlib
import json
from pathlib import Path

from evaluation.dataset import read_dataset

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'evaluation/datasets/test_verified.jsonl'
SOURCE = ROOT / 'evaluation/datasets/test_expansion_claims_draft_v2.jsonl'
EXPANSION = ROOT / 'evaluation/datasets/test_expansion_verified_v3.jsonl'
COMBINED = ROOT / 'evaluation/datasets/test104_verified_v1.jsonl'


def main():
    baseline = read_dataset(BASE, verified_only=True)
    rows = read_dataset(SOURCE)
    if len(baseline) != 52 or len(rows) != 52:
        raise ValueError('Expected 52 original and 52 expansion questions')
    byid = {r['id']: r for r in rows}
    byid['NEW04']['required_claims'] = ['z 表示共享，适用于多个容器共享。']
    byid['NEW06']['required_claims'] = ['低于 Linux 5.12 时显式指定 bind-recursive=readonly 会报错。']
    byid['NEW19']['required_claims'] = ['FOO 为 old。', 'BAR 为 new。', 'BAZ 为 new。']
    byid['NEW20']['required_claims'] = ['端口映射不需要且不支持。', '服务名 DNS 解析不工作。']
    byid['NEW21'].update(
        question='Compose 中有两个自定义网络：proxy 只连接前端网络，db 只连接后端网络，app 同时连接两个网络。根据文档，proxy 和 db 能否通过这两个网络直接通信？app 能否分别连接 proxy 和 db？',
        reference_answer='proxy 和 db 没有共同网络，按题设不能通过这两个网络直接通信；app 分别与 proxy 和 db 共享网络，可以分别连接。不能据此推断 app 会自动转发流量。',
        required_claims=['proxy 和 db 没有共同网络，因此不能通过题设网络直接通信。', 'app 分别与 proxy 和 db 共享网络，可以分别连接。'])
    byid['NEW23'].update(
        question='Compose Watch 已配置文件同步，但宿主机上的修改没有同步到容器目标目录。根据 Docker 文档，应检查容器运行用户的什么权限？能仅凭这一现象断定唯一原因吗？',
        reference_answer='应检查容器运行用户是否能够写入目标路径；仅凭同步失败不能确定唯一原因，文档还列有其他前提。',
        required_claims=['检查容器运行用户是否能写入目标路径。', '仅凭同步失败不能断定唯一原因。'])
    byid['NEW40']['required_claims'] = ['项目名为 alpha。']
    e = byid['NEW05']['evidence'][0]
    raw = ROOT / 'data/docker_official/raw/content/manuals/engine/storage/bind-mounts.md'
    lines = raw.read_text(encoding='utf-8').splitlines()
    e.update(line_end=463, excerpt='\n'.join(lines[e['line_start']-1:463]),
             source_url=e['source_url'].rsplit('#', 1)[0] + f"#L{e['line_start']}-L463")
    for row in rows:
        row.update(split='test_expansion', verification_status='verified', claim_version='reviewed_v3',
                   reference_review_note='用户认可题目和修订；助手依据固定版本 Docker 文档逐项核验。非独立盲法专家标注。')
    if len({r['id'] for r in baseline + rows}) != 104:
        raise ValueError('Duplicate IDs')
    if any(not r['required_claims'] or not r['evidence'] or not r['reference_answer'] for r in rows):
        raise ValueError('Missing claim, evidence, or reference')
    if any(not r.get('abstention_criteria') for r in rows if not r['answerable']):
        raise ValueError('Missing abstention criteria')
    # Do not overwrite earlier reviewed data or results.
    for path, items in ((EXPANSION, rows), (COMBINED, baseline + rows)):
        with path.open('x', encoding='utf-8', newline='\n') as handle:
            for row in items:
                handle.write(json.dumps(row, ensure_ascii=False) + '\n')
    for path in (EXPANSION, COMBINED):
        parsed = read_dataset(path, verified_only=True)
        print(path.name, len(parsed), hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
