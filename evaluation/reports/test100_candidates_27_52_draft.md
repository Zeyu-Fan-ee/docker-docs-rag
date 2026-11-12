# 新增题第二批：NEW27–NEW52 候选草稿

状态：待用户核验，尚未加入正式题集。文档为固定版本 `16e452c8eaea26cec842cbf1065037fb2015001f`；下列依据相对 `data/docker_official/raw/content/manuals/`。难度是预估，非实测。与既有问题共享主题或证据者如实标明；相似性和索引证据仍须入集前复查。环境题不能因检索失败判无答案。

用户复核记录（2026-11-10）：用户表示 NEW27–NEW52 均可通过。此记录表示用户认可当前草稿，不代表已完成逐题盲法独立核验；证据、索引和重复性复查以及正式入集仍待完成。

27. **[中等｜挂载限制]** 希望把容器镜像当作文件源挂进另一容器，并在里面修改这些文件。image mount 是否支持写入？**参考：**不支持，image mount 始终只读。**依据：** `engine/storage/image-mounts.md:54-57`。

28. **[中等｜故障排查]** 用 `--mount type=image` 挂载镜像，但该源镜像不在 daemon 镜像仓库。Docker 会自动拉取吗，应如何准备？**参考：**不会自动拉取，命令失败；先用 `docker pull` 拉取。**依据：** `engine/storage/image-mounts.md:59-68`。

29. **[综合｜兼容条件]** daemon 使用经典存储驱动时，可以使用 image mount 吗？`-v` 能代替它吗？**参考：**不能；image mount 要求 containerd image store，只能用 `--mount`，没有 `-v` 等价方式。**依据：** `engine/storage/image-mounts.md:70-74`。与 27–28 同主题但考查不同前提。

30. **[综合｜执行环境]** Alpine 容器从 image mount 运行动态链接的 glibc 程序失败，文档提示什么可能原因？**参考：**动态程序需要容器提供匹配的动态链接器和共享库；glibc 程序在基于 musl 的 Alpine 里可能不兼容。**依据：** `engine/storage/image-mounts.md:76-80`。需保留“可能”，不能仅凭症状断定根因。

31. **[比较｜存储机制]** VFS 存储驱动创建新层时使用 copy-on-write 吗？它如何创建新层、有什么代价？**参考：**不支持 COW；对父层做深拷贝，性能较低、磁盘占用更大。**依据：** `engine/storage/drivers/vfs-driver.md:9-14,72-74`。关联旧题 TEST09，但考查不同存储驱动。

32. **[中等｜平台限制]** 在 rootless Docker 上能使用 macvlan 驱动吗？**参考：**文档明确不支持 rootless 模式。**依据：** `engine/network/drivers/macvlan.md:24-32`。

33. **[综合｜排障]** macvlan 容器无法直接访问宿主机，文档提到什么原因？给出一种解决路径。**参考：**Linux 内核限制 macvlan 容器与宿主机直接通信；可同时连接 bridge 网络，或在主机上为相同 parent 创建 macvlan 接口并配置地址。**依据：** `engine/network/drivers/macvlan.md:47-52`。

34. **[中等｜网络选型风险]** 部署大量 macvlan 容器可能导致什么网络问题？物理设备需要具备什么能力？**参考：**可能造成 IP 耗尽或过多 MAC 地址（VLAN spread）；设备须能处理 promiscuous mode。**依据：** `engine/network/drivers/macvlan.md:34-41`。

35. **[中等｜网络条件]** Docker Desktop 使用 host 网络模式的最低版本和启用条件是什么？**参考：**Docker Desktop 4.34 及以上，需要在设置里启用。**依据：** `engine/network/drivers/host.md:36-42`。关联 NEW20，考查 Desktop 前提。

36. **[综合｜部署约束]** Swarm 服务使用 host 网络，每个服务容器要绑定宿主机 80 端口。在同一节点可同时运行多个该服务容器吗？**参考：**同一节点该端口只能由一个该服务容器绑定，因此最多一个；控制流量仍走 overlay，数据走宿主机网络。**依据：** `engine/network/drivers/host.md:48-54`。

37. **[中等｜配置默认值]** 创建 IPvlan 网络时不指定 `ipvlan_mode`，默认是什么？**参考：**`l2`。**依据：** `engine/network/drivers/ipvlan.md:80-95`。

38. **[综合｜网络排障]** IPvlan L2 模式中同一 parent 上两个不同子网无法互 ping，文档指出需要什么？**参考：**文档说明需要路由器为请求代理 ARP，并配置第二个子网；不能仅因同一 parent 就认为不同子网自动互通。**依据：** `engine/network/drivers/ipvlan.md:510-512`。

39. **[中等｜项目隔离]** 同一 CI 服务器上同时运行多个相同 Compose 项目的构建，怎样借助项目名减少互相干扰？**参考：**为每次构建设置唯一项目名，例如构建编号；Compose 用项目名隔离环境。**依据：** `compose/how-tos/project-name.md:19-25`。

40. **[综合｜配置优先级]** 同时设置 `-p alpha`、`COMPOSE_PROJECT_NAME=beta` 和顶层 `name: gamma` 时哪个项目名生效？**参考：**`alpha`，因为 `-p` 优先级最高。**依据：** `compose/how-tos/project-name.md:34-38`。与 TEST26 的容器环境变量优先级不同。

41. **[中等｜格式校验]** Compose 项目名可包含哪些字符？首字符有什么要求？**参考：**只能包含小写字母、数字、连字符、下划线，必须以小写字母或数字开头。**依据：** `compose/how-tos/project-name.md:27-32`。

42. **[综合｜插值条件]** `VAR` 已设置但值为空时，`${VAR:-fallback}` 和 `${VAR-fallback}` 分别得到什么？**参考：**前者得到 `fallback`；后者得到空值，因为变量已设置。**依据：** `compose/how-tos/environment-variables/variable-interpolation.md:45-50`。

43. **[综合｜插值条件]** `VAR` 已设置但为空，`${VAR:?error}` 和 `${VAR?error}` 哪个会退出报错？**参考：**带冒号的形式报错；不带冒号的形式因为变量已设置而返回空值。**依据：** `compose/how-tos/environment-variables/variable-interpolation.md:51-53`。关联 42，考查必填而非默认值。

44. **[中等｜多文件组织]** Compose 的 `include` 加载其他文件时，引用文件的相对路径按哪个项目目录解析？**参考：**每个被 include 文件作为独立 Compose 应用模型加载，使用自己的项目目录解析相对路径。**依据：** `compose/how-tos/multiple-compose-files/include.md:11-15`。关联 NEW17，但机制是 include 而非 `-f` 合并。

45. **[中等｜配置递归]** 一个被 Compose `include` 的文件自己又声明了 `include`，内部文件会被包含吗？**参考：**会；include 递归生效。**依据：** `compose/how-tos/multiple-compose-files/include.md:17-19`。

46. **[中等｜存储维护]** VFS 没有写时复制，新建镜像层是深拷贝父层。它适合作为其他存储后端测试时的什么用途？**参考：**可作为测试环境中验证其他存储后端的机制；代价是性能和磁盘使用。**依据：** `engine/storage/drivers/vfs-driver.md:9-14`。与 31 共享依据，需最终去重审查。

47. **[中等｜平台判断]** Docker Desktop for Windows 使用 Windows 容器时，可以按 macvlan 文档使用 macvlan 驱动吗？**参考：**不能；文档说 macvlan 仅适用于 Linux 主机，Docker Desktop Mac/Windows 和 Windows Engine 不支持。**依据：** `engine/network/drivers/macvlan.md:24-27`。与 32 主题关联，考查不同平台限制。

48. **[综合｜条件排查]** 创建 image mount 时源镜像存在，但 daemon 使用经典存储驱动；仅因为镜像存在就能成功吗？**参考：**不能；还需使用 containerd image store，且其他条件也须满足。**依据：** `engine/storage/image-mounts.md:59-74`。关联 28–29，是条件组合题，最终需审查是否值得单独保留。

49. **[中等｜插值来源]** Compose 没有传 `--env-file` 时会默认读取什么文件供插值？传入 `--env-file` 有什么变化？**参考：**默认读取 `.env`；显式 `--env-file` 指定并替代默认路径。**依据：** `compose/how-tos/environment-variables/variable-interpolation.md:176-178,201-208`。与 TEST27 区分插值和容器环境变量注入。

50. **[综合｜证据不足]** 文档说明 Docker Desktop 4.34 及以上可启用 host 网络，仅知道某同事使用 Docker Desktop，能确认其机器当前支持且已启用吗？**参考：**不能；还需知道版本、设置与适用环境。**依据：** `engine/network/drivers/host.md:36-42` 提供通用条件，题设缺具体状态；关联 35。

51. **[综合｜证据不足]** 根据两个 Compose 文件的合并规则，但只看到最终容器某环境变量值，看不到源文件，能唯一推断该值来自哪个文件吗？**参考：**不能；不同配置可以得到同一最终值，需要原始文件或其他证据。**依据：** `compose/how-tos/multiple-compose-files/merge.md:151-173`，题设缺输入内容；关联 NEW19。

52. **[综合｜证据不足]** Linux 容器执行 image mount 中的动态程序失败，是否能仅凭失败就认定一定是 glibc 与 musl 不兼容？**参考：**不能；文档列出运行时/动态链接器兼容性是可能原因，应查看程序、基础镜像及错误信息等。**依据：** `engine/storage/image-mounts.md:76-80`；与 30 同证据、不同诊断任务，入集前需审查是否过于相似。

## 复核要点

本批含多个主题内关联题：27–30、48、52 属于 image mount；31、46 均引用 VFS 机制；32–34、47 涉及 macvlan；42、43 均是插值中的空值条件。关联不等于完全重复，但不应把它们宣称为独立知识领域；最终应对照全部 64 道旧测试与开发题及第一批候选，删去缺乏新增信息的条目。用户确认后仍需复查题设、引用、索引与语义重复，并留待最终确定题集版本。
