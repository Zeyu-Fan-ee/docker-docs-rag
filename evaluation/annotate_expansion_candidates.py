"""Attach reviewable claim-level labels to expansion candidates, without freezing them."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = {
1: ['tmpfs 使用计入容器内存限制。', '增大 tmpfs 大小上限不会提高容器内存限制。'],
2: ['Docker tmpfs mount 不能在容器之间共享。'],
3: ['文档所述 tmpfs mount 功能仅在 Linux 上可用。'],
4: ['z 表示共享标签，适用于多个容器共享。', 'Z 表示私有、不共享。'],
5: ['--mount 不能修改 SELinux 标签。', '文档示例使用 -v 的 z 选项。'],
6: ['低于 Linux 5.12 时显式指定 bind-recursive=readonly 会报错。', '递归只读要求 Linux 5.12 或更高。'],
7: ['镜像层中的原文件不会被删除。', '容器层创建 whiteout 文件，使原文件在容器视图中不可见。'],
8: ['更换存储驱动后已有镜像和容器在本地变得不可访问。', '切换前可使用 docker save 保存镜像，或推送至镜像仓库。'],
9: ['自定义网络使用 --ipv6 和 --ipv4=false。', '默认 bridge 不能禁用 IPv4 地址配置。'],
10: ['默认绑定地址为 :: 时面向宿主机 IPv6 地址。', '默认绑定地址为 0.0.0.0 时面向宿主机 IPv4 和 IPv6 地址。'],
11: ['该选项控制容器间连通性。', '默认值为 true。'],
12: ['使用 docker network connect 将容器连接到已有网络。', '断开时不必先停止容器。'],
13: ['工作节点上的 overlay 网络不会自动删除。'],
14: ['即使是独立容器使用 overlay，Docker 主机也必须属于 Swarm。'],
15: ['使用 service_completed_successfully。'],
16: ['对 db 执行题设的显式 Compose 重启后，web 也会重启。'],
17: ['相对第一个基础文件 config/base.yaml 所在位置解析。', '使用相同 -f 参数运行 docker compose config 查看合并配置。'],
18: ['后定义的 command 替换前者，结果为 python worker.py。'],
19: ['FOO 为 old，BAR 为 new，BAZ 为 new。'],
20: ['容器共享宿主机网络栈。', '端口映射不需要且不支持。', '服务名 DNS 解析不工作。'],
21: ['proxy 与 db 没有共同网络。', 'app 同时加入两个网络。'],
22: ['使用 extra_hosts。', '映射添加到容器的 /etc/hosts。'],
23: ['容器运行用户必须能够写入目标路径。'],
24: ['在服务的 build.secrets 中授予 npm_token。', '在顶层 secrets 中将 npm_token 来源定义为 NPM_TOKEN 环境变量。'],
25: ['没有实际文件内容，无法确定最终镜像名。', '使用相同文件参数运行 docker compose config 查看合并配置，或查看实际配置文件。'],
26: ['无法仅凭已知信息确定 SELinux 标签就是故障根因。', '需要实际挂载参数、SELinux 标签或相关访问报错等证据。'],
27: ['image mount 始终只读，不能通过挂载修改镜像内容。'],
28: ['Docker 不会自动拉取缺失的源镜像，挂载命令会失败。', '先用 docker pull 获取源镜像。'],
29: ['image mount 需要 containerd image store，经典存储驱动不支持。', '只能用 --mount，不能用 -v 代替。'],
30: ['动态链接程序需要匹配的动态链接器和共享库。', 'glibc 程序在基于 musl 的 Alpine 中可能不兼容。'],
31: ['VFS 不支持写时复制。', '新层深拷贝父层。', '这种方式性能较低、磁盘占用较大。'],
32: ['macvlan 不支持 rootless 模式。'],
33: ['Linux 内核限制 macvlan 容器与宿主机直接通信。', '可同时连接 bridge 网络，或在宿主机上为同一 parent 创建 macvlan 接口并配置地址。'],
34: ['可能导致 IP 地址耗尽或过多 MAC 地址（VLAN spread）。', '网络设备需要能够处理 promiscuous mode。'],
35: ['Docker Desktop 版本须为 4.34 或以上。', '需要在设置中启用 host 网络功能。'],
36: ['同一节点不能同时运行多个都绑定该宿主机 80 端口的该服务容器。'],
37: ['默认模式是 l2。'],
38: ['文档给出使用路由器对请求执行 proxy ARP，并配置第二个子网。'],
39: ['为每次构建设置唯一 Compose 项目名，例如使用构建编号。'],
40: ['项目名为 alpha，因为 -p 的优先级最高。'],
41: ['只能包含小写字母、数字、连字符和下划线。', '首字符必须是小写字母或数字。'],
42: ['${VAR:-fallback} 得到 fallback。', '${VAR-fallback} 得到空值。'],
43: ['${VAR:?error} 退出并报错。', '${VAR?error} 不报错，返回空值。'],
44: ['被引入文件内部相对路径使用该被引入 Compose 应用模型自己的项目目录解析。'],
45: ['会，include 递归生效。'],
46: ['docker stack deploy 不支持 extends。'],
47: ['该场景不能使用 macvlan；文档说明 Windows 的 Docker Desktop 或 Docker Engine 不支持。'],
48: ['containerd image store 同时保留镜像的压缩层和解压层。', '文档说经典存储驱动只保存解压层。'],
49: ['不指定 --env-file 时默认读取 .env 用于插值。', '指定 --env-file 后使用指定的文件路径。'],
50: ['容器可以在镜像所有层完整下载前启动。', '远程 snapshotter 按需从镜像仓库获取层数据。'],
51: ['无法仅凭最终变量值唯一确定来源文件。', '需要查看实际配置文件或其他来源证据。'],
52: ['运行 docker compose build web 重建镜像。', '运行 docker compose up --no-deps -d web 重新部署。', '--no-deps 防止同时重新创建 web 依赖的服务。'],
}
ABSTENTION = {
25: '不得断言未知的最终镜像名；应指出缺少实际文件并建议检查合并配置。',
26: '不得断言 SELinux 标签一定是根因；应说明证据不足并指出需要的排查信息。',
51: '不得断言最终值唯一来自某个文件；应说明需要实际文件或其他来源证据。',
}


def main():
    input_path = ROOT / 'evaluation/datasets/test_expansion_candidates_v1.jsonl'
    output_path = ROOT / 'evaluation/datasets/test_expansion_claims_draft_v2.jsonl'
    rows = [json.loads(line) for line in input_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    if len(rows) != 52 or set(CLAIMS) != set(range(1, 53)):
        raise ValueError('Expected 52 candidates and 52 claim mappings')
    for row in rows:
        n = int(row['id'][3:])
        row['required_claims'] = CLAIMS[n]
        row['reference_review_note'] = '必答点已拆分；仍待原文和实际切片逐项复核，未经正式冻结。'
        if n in ABSTENTION:
            row['abstention_criteria'] = ABSTENTION[n]
        if n == 13:
            row['reference_answer'] = '工作节点按需自动创建 overlay 网络，但不会自动删除。'
        row['claim_version'] = 'draft_v2'
    with output_path.open('x', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')
    print(f'Created {len(rows)} pending candidates, {sum(len(r["required_claims"]) for r in rows)} proposed claims')


if __name__ == '__main__':
    main()
