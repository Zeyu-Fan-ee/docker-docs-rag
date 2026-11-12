# 新增题修订和替换草稿 v1

2026-11-10：用户同意对 NEW14、NEW36、NEW38、NEW44 调整，并替换 NEW46、NEW48、NEW50、NEW52。下面是新提案，待用户逐项确认；原草稿及用户原先认可的记录保留，以便追溯。未修改原 52 题，未正式入集。引用为固定 Docker 文档版本 `16e452c8eaea26cec842cbf1065037fb2015001f`。

复核记录（2026-11-10）：用户认可上述四道调整和四道替代题。用户认可不表示已完成独立盲法标注；正式入集前仍须逐题复核证据、切片内容和语义重复。

## 四道原题的调整

**NEW14 — 独立容器的 overlay 前提。** 问题不变：只让独立容器使用 overlay 而不创建 Swarm 服务，主机是否需要加入 Swarm？参考答案：需要。唯一必答点为「主机必须属于 Swarm」；`--attachable` 可作为正确的补充，不因未提及而扣分。依据：`engine/network/drivers/overlay.md:35-38,49-58`。

**NEW36 — host 端口占用。** 问题不变：Swarm 服务用 host 网络，同一节点服务容器均要绑定 80 端口，能运行多个吗？参考答案：不能，同一节点该端口最多由一个这样的容器绑定。控制流量与数据流量的区别可作为补充，不列为必答点。依据：`engine/network/drivers/host.md:48-54`。

**NEW38 — IPvlan L2 示例。** 修改问题：Docker 文档的 IPvlan L2 示例中，同一 parent 的不同子网不能互 ping；文档给出了哪一种路由解决方式？参考答案：使用路由器对请求执行 proxy ARP，并配置第二个子网。限定为文档中的方式，不判定其他路由方案一定不可行。依据：`engine/network/drivers/ipvlan.md:508-513`。

**NEW44 — include 内部路径。** 修改问题：Compose 通过 `include` 引入另一个 Compose 文件时，被引入文件**内部的相对路径**按哪个项目目录解析？参考答案：被引入文件作为独立 Compose 应用模型加载，使用它自己的项目目录解析内部相对路径。依据：`compose/how-tos/multiple-compose-files/include.md:11-15`。

## 四道替代题

**NEW46-R — stack 部署兼容性（中等，条件判断）**

问题：Compose 文件使用了 `extends`。根据 Docker 文档，能直接用 `docker stack deploy` 部署该配置吗？

参考答案：不能；文档说明 `docker stack deploy` 不支持 `extends`，`docker stack config` 处理这类文件会报告配置包含禁止的属性。

必答点：stack deploy 不支持 `extends`。报错文本可作补充。解释：Compose 中能复用配置，不代表每一种部署入口都支持同一语法。

依据：`compose/how-tos/multiple-compose-files/extends.md:30-34`。与 NEW44 均是多文件机制，但分别考查 `extends` 的部署兼容性与 `include` 路径。

**NEW48-R — containerd 磁盘占用（中等，原理解释）**

问题：同样的镜像为什么使用 containerd image store 时可能比经典存储驱动占用更多磁盘？

参考答案：containerd 同时保留从镜像仓库获取的压缩层及解压后的层；文档说经典驱动只保存解压层，因此需要更多磁盘空间。

必答点：同时存压缩和解压层；与经典存储驱动作出对应比较。解释：像同时保留压缩包和解压后的文件，自然要占更多空间。

依据：`engine/storage/containerd.md:45-55`。与原 NEW48、NEW29 的 image mount 兼容条件不同。

**NEW50-R — 延迟拉取（中等，机制判断）**

问题：启用 lazy pulling 后，容器必须等镜像的所有层都下载完成才能启动吗？未提前下载的内容怎样取得？

参考答案：不必；容器可以在镜像完整下载前启动，远程 snapshotter 按需从镜像仓库获取层数据。

必答点：可在完全下载前启动；需要时获取层数据。解释：先启动，使用到某些内容时再取，而不是等所有内容下载完。

依据：`engine/storage/containerd.md:116-119`。不声称所有 snapshotter 默认都启用 lazy pulling。

**NEW52-R — Compose 重部署（综合，操作与影响）**

问题：Docker 文档中，修改代码后要重新部署 Compose 服务 `web`，且不重新创建它依赖的服务，示例使用哪些命令？`--no-deps` 起什么作用？

参考答案：先运行 `docker compose build web`，再运行 `docker compose up --no-deps -d web`；`--no-deps` 防止 Compose 同时重新创建 web 依赖的服务。

必答点：重建 web 镜像；带 `--no-deps` 重新部署 web；说明不同时重新创建依赖服务。解释：只更新 web，避免 web 所依赖的数据库等服务也被跟着重新创建。

依据：`compose/how-tos/production.md:45-58`。这替换原先的证据不足题，因此最终拒答题数量会变化，应如实统计。

## 检查边界

三份替代题文档路径在现有切片清单中均存在：`extends.md` 13 片、`containerd.md` 15 片、`production.md` 6 片。这仅说明对应文档已切片，尚不能代替逐项证据、数据库内容及题目独立性复核。标签是设计难度而非实测表现。
