# 开发集小批量校准记录

本次使用 DEV01、DEV02、DEV03，固定已构建的 Docker 知识库，启用重排生成答案。
这是开发集调试，不是正式测试结果。

| 问题 | 人工对照观察 | 待核验之处 |
|---|---|---|
| DEV01 volume 删除后是否保留 | 回答说会保留，但没有说明 `--rm` 清理关联匿名卷的例外。 | 此次实际 Top-3 上下文缺少直接说明该例外的片段，需要继续检查召回和排序。 |
| DEV02 何时使用 bind mount | 回答提到了从宿主机和容器访问文件，未具体举出开发共享代码等例子。 | 根据已约定规则检查例子和宿主机路径依赖是否覆盖。 |
| DEV03 tmpfs 是否持久化 | 回答包含容器停止后数据不保留和 swap 可能写入文件系统。 | 个别表述将“不会持久化”与 swap 例外放在一起，需要复核是否造成误解。 |

## RAGAS 状态

评测依赖安装于独立 `.venv-eval`。RAGAS 0.4.3 和三个指标可导入，`pip check` 无依赖冲突。
首次 DEV01 校准，Faithfulness 返回 IncompleteOutputException，另外两项返回 RateLimitError。
提高输出上限后，仅重试 Factual Correctness，仍返回 RateLimitError。
随后发送一次短测试请求，接口仍返回 HTTP 429，未提供可读取的重试时间或具体配额信息；此后停止请求。
未取得有效分数；这些错误不是 0 分。错误的确切账户配额原因需要在服务商控制台确认。
生成和评测均使用同一个 Gemini 模型，模型评分仍需对照人工结果。

运行数据：`../results/dev_pilot_3.jsonl`。
首次错误：`../results/dev_pilot_first_scores.jsonl`。
单指标重试：`../results/dev_pilot_first_retry.jsonl`。
