# Judge 事实判断校准集草稿 v1

状态：用户于 2026-11-09 表示认可校准组 CAL01–CAL04 的判断；验证组 VAL01–VAL04 仍待核验。题目及判断草稿由助手依据项目内 Docker 文档拟定，用户是在看到草稿判断后认可，因此不是盲法独立人工标注，也不是 RAGAS 测试结果。每题两个回答变体，按题分组，避免同一题的变体同时进入校准组和验证组。校准组 01–04，验证组 05–08；两组均属小样本，不能据此推断总体准确率。

核验方式：先独立阅读问题、回答和文档证据，记录判断和理由，再查看 Judge 结果。重点分别记录：必要事实有无覆盖、回答中每个额外事实是否正确、证据不足时是否应判待查。拒答是否合适单独判断，不直接等同于标准 RAGAS Factual Correctness 的数值。允许多种正确表达；不以文字相似度判断正确。

## 校准组

### CAL01 — 等价命令
问题：如何用 `--mount` 把名为 `myvol` 的卷只读挂载到 nginx 容器的 `/data`？
参考要点：卷名 myvol，容器路径 /data，只读；source/src、destination/dst/target 和 readonly/ro 是对应别名。
- A：`docker run --mount type=volume,source=myvol,destination=/data,readonly nginx`。预期：正确。
- B：`docker run --mount type=volume,src=myvol,target=/data,ro nginx`。预期：正确，不能因写法不同判错。
证据：`data/docker_official/raw/content/manuals/engine/storage/volumes.md` 143–146 行。

### CAL02 — 缺失必要条件
问题：对使用 XFS 的 overlay2，Docker 文档要求什么文件系统条件？
参考要点：XFS 须启用 d_type 支持，格式化时可使用 `-n ftype=1`。
- A：XFS 需要支持 d_type；格式化时可使用 `-n ftype=1`。预期：正确。
- B：只要底层文件系统是 XFS 就可以使用 overlay2。预期：错误，漏掉关键条件且说得过于绝对。
证据：`data/docker_official/raw/content/manuals/engine/storage/drivers/overlayfs-driver.md` 28–32 行。

### CAL03 — 额外事实
问题：Docker 的 none 网络驱动会创建什么网络设备？
参考要点：只创建 loopback 设备。
- A：只创建 loopback；该驱动不会为容器配置 IPv6 loopback 地址。预期：正确；后半句是文档支持的额外事实，不应仅因参考答案没写而扣分。
- B：只创建 loopback；该驱动默认会配置 IPv6 loopback 地址。预期：包含错误额外事实，应标记错误，不能仅因核心事实正确就放过。
证据：`data/docker_official/raw/content/manuals/engine/network/drivers/none.md` 9–23 行。

### CAL04 — 保留版本条件
问题：把端口发布到 localhost 时，Docker 28.0.0 之前有哪些访问风险？
参考要点：旧于 28.0.0 时，同一二层网络中的其他主机可能访问发布到 localhost 的端口。
- A：在 28.0.0 之前，同一二层网络的其他主机可能访问该端口。预期：正确。
- B：任何版本中任何远程主机都一定不能访问该端口。预期：错误，忽略版本例外且过度绝对。
证据：`data/docker_official/raw/content/manuals/engine/network/port-publishing.md` 50–57 行。

## 验证组（核验后冻结；调整 Judge 时不使用其标签）

### VAL01 — 端口与协议
问题：`docker run -p 8080:80` 发布的是哪种协议的哪个端口？
参考要点：主机 8080 映射到容器 TCP 80。
- A：容器的 TCP 80 映射到宿主机的 8080。预期：正确。
- B：容器的 UDP 80 映射到宿主机的 8080。预期：错误，协议不对。
证据：`data/docker_official/raw/content/manuals/engine/network/port-publishing.md` 35–38 行。

### VAL02 — 性能条件
问题：给 overlay 网络启用加密有什么性能影响？
参考要点：有不可忽略的性能损耗，应针对实际场景测试。
- A：会有明显的性能代价，实际使用前应测试。预期：正确。
- B：加密没有性能损耗。预期：错误。
证据：`data/docker_official/raw/content/manuals/engine/network/drivers/overlay.md` 63–79 行。

### VAL03 — 特定平台限制
问题：Docker 支持在 Windows 上使用 overlay 网络加密吗？
参考要点：Windows 上不支持 overlay 网络加密。
- A：不支持 Windows 上的 overlay 网络加密。预期：正确。
- B：支持，而且 Windows 容器之间的数据一定会加密。预期：错误。
证据：`data/docker_official/raw/content/manuals/engine/network/drivers/overlay.md` 80–90 行。

### VAL04 — 正确拒答与虚构
问题：我们公司生产环境中名叫 `finance-db` 的 Docker 卷里具体有哪些客户数据？
给定证据：仅有公开 Docker 文档，无公司生产环境数据。
参考要点：现有证据无法确定，需要查看授权的实际环境或资料。
- A：根据现有资料无法确定，需要查看有权限的实际环境。预期：恰当拒答。
- B：该卷中存有客户姓名、银行卡号和交易记录。预期：无证据支持的具体断言；不能认定事实正确。
证据：此题以给定证据范围为前提；公开 Docker 文档并不提供该公司的私有环境内容。不能仅凭缺少证据断言 B 在现实中必然为假。

## 下一步人工记录

逐项填写：核验人、日期、判断（正确 / 错误 / 证据不足）、具体理由、文档依据、是否同意草稿。确认后冻结验证组；再对校准组调整 Judge 配置，用验证组一次性检查事实判断一致性、错误类型和重复评分稳定性。正式 52 题、参考答案、既有生成答案及原始 0.240 结果均保持原样。
