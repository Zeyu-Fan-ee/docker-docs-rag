# 评测工作区

> 当前结果：已使用 `datasets/test104_verified_v1.jsonl` 完成 104 题生成及 93 道可回答题的 Qwen-Plus RAGAS 评分，11 道证据不足题单独核查。方法、结果及边界见 `reports/test104_qwen_review_v1.md`。下方保留早期评测操作与规范，历史状态描述不代表当前进度。

`datasets/dev_candidates.jsonl` 是待人工核验的开发题，不是 Ground Truth。
先逐题填写 reference_answer、required_claims 和 evidence（原文 URL、行号、引文），核对后将 verification_status 改为 verified。
无答案题需要检查整个知识范围，不能因为检索器没找到就标注为无答案。

正式 test 集另建并冻结，建议至少 50 题；相同问题的改写或共享证据的近似题不要分到 dev/test 两侧。
本目录数据不会被知识库解析器读取。正式评测期间停止上传，固定 corpus commit、chunking、索引、模型和 Prompt。

运行（项目根目录，使用当前虚拟环境 Python）：

```powershell
python -m evaluation.run --dataset evaluation/datasets/dev_candidates.jsonl --output evaluation/results/dev_baseline.jsonl --no-reranker
python -m evaluation.run --dataset evaluation/datasets/dev_candidates.jsonl --output evaluation/results/dev_rerank.jsonl
# 安装 requirements-eval.txt 并明确配置 JUDGE_* 后，小批量评分会产生 API 费用
python -m evaluation.score_ragas --input evaluation/results/dev_rerank.jsonl --output evaluation/results/dev_scores.jsonl
python -m evaluation.summarize --input evaluation/results/dev_scores.jsonl --output evaluation/reports/dev_summary.json
```

未核验题会被排除；没有已核验题时运行器拒绝启动。输出文件存在时拒绝覆盖。
每次运行保存原问题、改写问题、原始候选、完整重排、实际上下文、引用、耗时、配置和可获得的 token 用量。
费用取决于提供商价格，代码不伪造费用；多轮改写用量暂未合并到生成 usage 中。
早期 RAGAS 试评曾遇到输出不完整及 API 限流，详见 `reports/dev_pilot_manual_review.md`；后续正式评分结果见上方当前结果。

评测依赖位于 `.venv-eval`，按 `requirements-eval.txt` 固定兼容版本；原问答依赖仍位于 `.venv`。评分需要单独配置 `JUDGE_*`。如果临时复用现有生成模型配置，应只在进程环境中映射，避免将密钥写入结果文件。

## 人工评分规范 v1

- 正确性：0 核心错误；1 部分正确但有重要问题；2 必要事实正确且无重大错误。
- 完整性：必要要点覆盖数 / 必要要点总数，注明遗漏。
- 依据性：逐项检查断言是否被实际上下文支持。
- 引用：分别检查编号有效、位置有效、引用内容是否支持关联断言。
- 拒答：无答案题是否说明证据不足；可回答题是否错误拒答。

无答案题单独评审，不把 Context Recall 的空参考分母设为普通 0 分。
报告有效评分条数、失败条数及原因；模型评分失败不等于回答错误。
比较策略时逐题配对，报告总体及题型分组；50 题中一题就是 2 个百分点，避免过度解释微小差异。
