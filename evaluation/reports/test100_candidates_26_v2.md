# 新增评测题第一批：26 道候选题 v2

状态：候选草稿，等待用户复核；未计入已核验正式题集。难度为初步设计标签：基础=单条规则；中等=条件或选择；综合=结合多条规则或多个约束，并不代表实测模型难度。文档版本为 `16e452c8eaea26cec842cbf1065037fb2015001f`。下列引用路径均相对于 `data/docker_official/raw/content/manuals/`，行号供对照固定版本。与原 52 题或开发题共享主题者注明关联，不能当作严格独立主题。原题和记录未修改。

复核记录（2026-11-10）：用户先表示除第 8、13、14 题外其他题没有问题；对第 8 题调整措辞、解释第 13 和 14 题后，用户确认。26 题因此获用户认可；正式入集之前仍须完成证据、索引和重复性复查。

1. **[中等｜资源条件]** Linux 容器设置了内存限制，又把 tmpfs 的大小上限设置得很大。后者会让容器获得限制之外的额外内存吗？**要点：**不会；tmpfs 使用计入容器内存限制，填满仍可能导致 OOM。**依据：** `engine/storage/tmpfs.md:20-26`。关联 DEV03，考查不同的内存限制。

2. **[中等｜限制与选型]** 两个容器需要共享同一份数据，Docker 的 tmpfs mount 能像 volume 一样直接共享吗？**要点：**不能；Docker 文档说明 tmpfs mount 不能在容器间共享。**依据：** `engine/storage/tmpfs.md:53-56`。关联 TEST11，但对象是 tmpfs 的限制。

3. **[基础｜平台条件]** Docker 文档所述 tmpfs mount 需要什么平台？**要点：**该功能仅在运行 Docker 的 Linux 环境可用。**依据：** `engine/storage/tmpfs.md:53-56`。关联 DEV03。

4. **[中等｜安全配置比较]** Linux 使用 SELinux 的 bind mount，需要多个容器共享同一挂载内容时，文档中的 `z` 和 `Z` 应选哪个？**要点：**`z` 表示共享标签；`Z` 表示私有、不共享。**依据：** `engine/storage/bind-mounts.md:432-441`。

5. **[综合｜安全与语法限制]** 在 SELinux 环境，想按 Docker 文档使用 `z` 修改 bind mount 标签，却打算使用 `--mount`。这个标志支持修改标签吗？文档示例使用哪类写法？**要点：**`--mount` 不能修改 SELinux 标签；文档示例使用 `-v` 的 `z` 选项。**依据：** `engine/storage/bind-mounts.md:432-456`。与第 4 题主题关联，考查语法限制。

6. **[综合｜版本条件]** 低于 Linux 5.12 的内核上，对只读 bind mount 显式指定 `bind-recursive=readonly`，结果是什么？**要点：**递归只读需要内核 5.12 或更高；在较低版本显式启用会报错。**依据：** `engine/storage/bind-mounts.md:345-354`。关联 TEST33，考查显式开启而非默认行为。

7. **[中等｜文件系统原理]** 使用 overlay2 删除只存在于只读镜像层的文件，镜像层里的原文件会被删除吗？容器视图怎样隐藏它？**要点：**镜像层不被删除；容器层创建 whiteout 文件，隐藏原文件。**依据：** `engine/storage/drivers/overlayfs-driver.md:382-390`。

8. **[中等｜迁移前检查]** 根据 Docker 文档，在更换 Docker 存储驱动之前，已有镜像和容器会受到什么影响？为避免镜像需要重新构建，切换前可以怎么做？**要点：**已有镜像和容器在本地变得不可访问；文档建议提前用 `docker save` 保存镜像，或推送至 Docker Hub / 私有 registry。文档这里并未说镜像和容器被删除；上述方法针对镜像，不能当作容器数据备份。**依据：** `engine/storage/drivers/overlayfs-driver.md:33-37`。

9. **[中等｜网络条件]** 创建只使用 IPv6 的用户自定义 bridge 网络需要哪些选项？默认 bridge 能禁用 IPv4 地址配置吗？**要点：**创建时使用 `--ipv6 --ipv4=false`；默认 bridge 不能禁用 IPv4 地址配置。**依据：** `engine/network/drivers/bridge.md:246-255`。

10. **[综合｜网络安全条件]** Docker bridge 默认发布地址设成 `::` 和设成 `0.0.0.0`，文档说它们分别对哪些地址族开放？**要点：**`::` 为宿主机 IPv6 地址；`0.0.0.0` 为宿主机 IPv4 和 IPv6 地址。**依据：** `engine/network/drivers/bridge.md:149-165`。这是默认绑定设置，区别于 TEST01 的明确 IPv4 回环绑定。

11. **[中等｜网络配置]** 自定义 bridge 网络的 `com.docker.network.bridge.enable_icc` 是做什么的？默认值是什么？**要点：**控制容器间连通性，默认 `true`。**依据：** `engine/network/drivers/bridge.md:113-125`。

12. **[中等｜网络动态操作]** 容器已经运行，如何让它加入一个现有的用户自定义 bridge 网络？文档中断开时容器必须先停止吗？**要点：**使用 `docker network connect`；可以在容器运行时连接或断开。**依据：** `engine/network/drivers/bridge.md:68-76,202-225`。关联 DEV05，考查具体操作。

13. **[中等｜生命周期]** Swarm 工作节点按需创建了 overlay 网络后，文档说它会在不使用时自动删除吗？**要点：**文档说工作节点按需自动创建 overlay 网络，但不会自动删除。**解释：**网络是连接多台 Docker 主机的虚拟网络，工作节点是 Swarm 集群中的机器；文档指出自动创建不等于自动清理。此处不推断网络一定可安全删除。**依据：** `engine/network/drivers/overlay.md:15-18,287-291`。

14. **[中等｜部署前提]** 即使只让独立容器使用 overlay 网络而不创建 Swarm 服务，Docker 主机还需要加入 Swarm 吗？**要点：**需要；独立容器也有这一主机前提。让独立容器连接该 overlay 网络还需要创建时设置 `--attachable`。**解释：**Swarm 是 Docker 的集群模式；独立容器是直接运行、不是由 Swarm 服务管理的容器。主机加入 Swarm 和允许独立容器加入网络是两个不同条件。**依据：** `engine/network/drivers/overlay.md:35-38,49-58`。关联 TEST17（考查 `--attachable`），本题主要考查主机前提。

15. **[基础｜服务生命周期]** 在 Compose 中，前置任务必须成功执行完后才启动依赖服务，应使用哪个 `depends_on` condition？**要点：**`service_completed_successfully`。**依据：** `compose/how-tos/startup-order.md:18-26`。关联 DEV07，考查成功结束而非健康状态。

16. **[中等｜条件判断]** Docker 文档的 Compose 示例里 web 对 db 的 `depends_on` 设置 `restart: true`。使用 `docker compose restart` 显式重启 db，web 会怎样？**要点：**web 也会重启；该结论限定文档所说的显式 Compose 操作。**依据：** `compose/how-tos/startup-order.md:32-37,52-56`。关联 DEV07。

17. **[综合｜配置排障]** 使用 `docker compose -f config/base.yaml -f overrides/dev.yaml` 时，override 文件中的相对路径应相对哪个文件解析？怎样查看合并后的配置？**要点：**相对第一个基础文件 `config/base.yaml`；可使用相同 `-f` 参数运行 `docker compose ... config`。**依据：** `compose/how-tos/multiple-compose-files/merge.md:21-28,70-81`。

18. **[中等｜合并规则]** 两个 Compose 文件按先后顺序合并，前一个 service 的 `command` 是 `python app.py`，后一个是 `python worker.py`，结果是什么？**要点：**单值字段后者替换前者，结果是 `python worker.py`。**依据：** `compose/how-tos/multiple-compose-files/merge.md:83-87`。

19. **[综合｜配置推断]** 两个 Compose 文件合并：前一个环境变量为 `FOO=old, BAR=old`，后一个为 `BAR=new, BAZ=new`。按文档示例，最终三个值是什么？**要点：**FOO=old、BAR=new、BAZ=new；按变量名合并，后定义的同名值优先。**依据：** `compose/how-tos/multiple-compose-files/merge.md:151-184`。关联 TEST26/48，但这里是文件合并而非变量来源优先级。

20. **[中等｜网络模式]** Compose 服务使用 `network_mode: host` 后，文档如何说明端口映射和服务名 DNS？**要点：**共享宿主机网络栈；端口映射不需要且不支持，服务名 DNS 解析不工作。**依据：** `compose/how-tos/networking.md:60-63`。关联 DEV06，但考查端口映射和 DNS。

21. **[中等｜网络隔离]** Compose 有两个网络：proxy 只加入前端网络，db 只加入后端网络，app 加入两者。为什么 proxy 与 db 隔离，哪个服务连接两边？**要点：**proxy 与 db 没有共同网络；app 同时加入两者。**依据：** `compose/how-tos/networking.md:90-94`。

22. **[基础｜配置操作]** Compose 给容器添加固定的主机名到 IP 映射，可以用什么配置？它添加到容器哪个文件？**要点：**`extra_hosts`；容器内 `/etc/hosts`。**依据：** `compose/how-tos/networking.md:263-265`。

23. **[综合｜排障]** Compose Watch 配置了文件同步，但容器内运行用户不能写入目标目录。按照文档，应该检查什么权限条件？**要点：**容器的 `USER` 必须能写入目标路径，调整目录权限或属主使其可写。**依据：** `compose/how-tos/file-watch.md:49-56`。关联 DEV10，考查写入权限而非版本要求。

24. **[中等｜敏感信息与构建]** Compose 示例里，要在构建时使用来自 `NPM_TOKEN` 环境变量的 secret，应在哪里为构建授予该 secret，并在哪里定义它的来源？**要点：**服务的 `build.secrets` 指定 `npm_token`；顶层 `secrets` 定义 `npm_token` 来源为 `NPM_TOKEN` 环境变量。**依据：** `compose/how-tos/use-secrets.md:97-112`。关联 DEV08，考查构建时而非运行时授权。

25. **[综合｜证据边界]** 文档说把 Compose 多文件按顺序合并；只知道执行了 `docker compose -f base.yaml -f dev.yaml up`，但没有两个文件内容，能确定最后服务使用的镜像名吗？还能提出什么检查方式？**要点：**无法确定具体镜像名；需要实际文件，可使用相同文件参数运行 `docker compose config` 查看合并结果。**依据：** `compose/how-tos/multiple-compose-files/merge.md:21-28,70-87`。与常见“生产状态未知”题不同，考查缺失配置内容。

26. **[综合｜证据边界]** 文档说明 SELinux 的 `z` 用于共享、`Z` 用于私有。只知道某服务挂载目录但不知道其实际挂载参数和标签，能断定 SELinux 标签导致了访问失败吗？下一步需要什么信息？**要点：**不能确定根因；需要实际挂载参数、SELinux 标签及相关访问报错等证据。**依据：** `engine/storage/bind-mounts.md:432-441` 为一般规则；题设缺实际信息。与 DEV12 的泛化故障拒答相关，但增加了具体排查证据。

## 核验注意

题目覆盖存储、网络、Compose、版本/平台条件和证据边界；覆盖和难度标签尚待复核。所有答题要点应以标注位置的固定版本文档为准，复杂题要逐项检查；等价写法可接受。新增题与既有测试及开发题存在已标注关联，不应将这 26 题宣称为彼此完全独立。正式采用前核对原文、索引包含性、是否重复及题设歧义；拒答依据是题设缺失具体信息，而非检索没找到。若用户认可后发现真实证据冲突，需修正并保留记录。
