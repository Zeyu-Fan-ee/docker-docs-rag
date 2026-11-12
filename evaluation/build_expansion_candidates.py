"""Convert reviewed Markdown candidates into an explicitly unverified JSONL draft."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = '16e452c8eaea26cec842cbf1065037fb2015001f'
SOURCES = ('evaluation/reports/test100_candidates_26_v2.md',
           'evaluation/reports/test100_candidates_27_52_draft.md')

REVISED = {
    14: ('即使只让独立容器使用 overlay 网络而不创建 Swarm 服务，Docker 主机还需要加入 Swarm 吗？', '需要，Docker 主机必须属于 Swarm。', 'engine/network/drivers/overlay.md', '35-38'),
    36: ('Swarm 服务使用 host 网络，每个服务容器要绑定宿主机 80 端口。在同一节点可同时运行多个该服务容器吗？', '不能，同一节点该端口最多由一个这样的服务容器绑定。', 'engine/network/drivers/host.md', '48-54'),
    38: ('Docker 文档的 IPvlan L2 示例中，同一 parent 的不同子网不能互 ping；文档给出了哪一种路由解决方式？', '使用路由器对请求执行 proxy ARP，并配置第二个子网。', 'engine/network/drivers/ipvlan.md', '508-513'),
    44: ('Compose 通过 include 引入另一个 Compose 文件时，被引入文件内部的相对路径按哪个项目目录解析？', '被引入文件作为独立 Compose 应用模型加载，使用自己的项目目录解析内部相对路径。', 'compose/how-tos/multiple-compose-files/include.md', '11-15'),
    46: ('Compose 文件使用了 extends。根据 Docker 文档，能直接用 docker stack deploy 部署该配置吗？', '不能；文档说明 docker stack deploy 不支持 extends。', 'compose/how-tos/multiple-compose-files/extends.md', '30-34'),
    48: ('同样的镜像为什么使用 containerd image store 时可能比经典存储驱动占用更多磁盘？', 'containerd 同时保留镜像的压缩层和解压后的层；文档说经典存储驱动只保存解压层。', 'engine/storage/containerd.md', '45-55'),
    50: ('启用 lazy pulling 后，容器必须等镜像的所有层都下载完成才能启动吗？未提前下载的内容怎样取得？', '不必；容器可以在镜像完整下载前启动，远程 snapshotter 按需从镜像仓库获取层数据。', 'engine/storage/containerd.md', '116-119'),
    52: ('Docker 文档中，修改代码后要重新部署 Compose 服务 web，且不重新创建它依赖的服务，示例使用哪些命令？--no-deps 起什么作用？', '先运行 docker compose build web，再运行 docker compose up --no-deps -d web；--no-deps 防止 Compose 同时重新创建 web 依赖的服务。', 'compose/how-tos/production.md', '45-58'),
}


def main():
    pattern = re.compile(r'^([0-9]+)\. \*\*\[(.*?)\]\*\* (.*?)\*\*(?:要点|参考)：\*\*(.*?)\*\*依据：\*\* `((?:engine|compose)/[^`]+?\.md):([0-9,-]+)`', re.M)
    matches = []
    for filename in SOURCES:
        matches.extend(pattern.findall((ROOT / filename).read_text(encoding='utf-8')))
    if len(matches) != 52 or len({int(m[0]) for m in matches}) != 52:
        raise ValueError('Expected exactly 52 uniquely numbered candidates')
    rows = []
    for number, tags, question, answer, path, intervals in sorted(matches, key=lambda x: int(x[0])):
        n = int(number)
        if n in REVISED:
            question, answer, path, intervals = REVISED[n]
        raw = ROOT / 'data/docker_official/raw/content/manuals' / path
        lines = raw.read_text(encoding='utf-8').splitlines()
        evidence = []
        for span in intervals.split(','):
            numbers = [int(x) for x in span.split('-')]
            start, end = numbers[0], numbers[-1]
            if not (1 <= start <= end <= len(lines)):
                raise ValueError(f'Invalid evidence range: NEW{n:02}')
            evidence.append(dict(source_url=f'https://github.com/docker/docs/blob/{REVISION}/content/manuals/{path}#L{start}-L{end}',
                                 line_start=start, line_end=end, excerpt='\n'.join(lines[start-1:end])))
        answerable = n not in {25, 26, 51}
        rows.append(dict(id=f'NEW{n:02}', split='candidate', verification_status='pending', category=tags,
                         question=question.strip(), reference_answer=answer.strip(), required_claims=[],
                         answerable=answerable, evidence=evidence, corpus_revision=REVISION,
                         reference_review_note='用户已认可草稿；必答点尚需逐项拆分并核验，未用于正式评测。',
                         replaced=(n in {46, 48, 50, 52})))
    output = ROOT / 'evaluation/datasets/test_expansion_candidates_v1.jsonl'
    with output.open('x', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')
    print(f'Wrote {len(rows)} pending candidates, {sum(x["answerable"] for x in rows)} answerable, {sum(not x["answerable"] for x in rows)} evidence-insufficient')


if __name__ == '__main__':
    main()
