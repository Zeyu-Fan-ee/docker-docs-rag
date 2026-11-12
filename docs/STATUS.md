# 当前进度与下一步

> 历史记录：以下内容记录 2026-11-06 的阶段状态，不代表当前进度。之后已完成 104 题评测及 Docker 本机部署；最新概况见项目 README 和 `evaluation/reports/test104_qwen_review_v1.md`。

截至 2026-11-06，已完成工程准备、全量 Docker 建库与真实检索/重排检查；尚未完成真实 LLM 端到端问答验收和正式评测。

## 已完成

- 复用现有 Python 工程；配置、解析、切分、入库、检索、生成、API、UI 与评测明确分工。
- 保留 Docker 原文 54 个文件、固定 commit、来源和哈希；排除 1 个无正文导航页。
- 补齐 5 个正文 include，以及同 commit 的功能版本元数据和模板配置。
- 53 篇有效正文 + 5 个支持片段，解析为 547 个章节、510143 个字符；未处理模板为 0。
- Markdown 保留标题、代码块、表格文本、原文章节行号和官方来源；Go 模板不误删。
- PDF 按页解析；DOCX 段落与表格按顺序读取；MD/TXT/PDF/DOCX 使用同一入库流程。
- 配置化模型、设备、Top-K、final-K、重排开关、切分方法；可进行有/无重排对比。
- 新增 token 长度保护、逐文档稳定 ID、索引处理指纹和构建状态检查。
- 后端支持无索引启动；/health 与 /ready 区分服务存活和索引就绪。
- UI 支持来源 URL 和上传；保留多轮改写与 SSE 流式回答。
- 离线运行器保存候选、重排、实际上下文、答案、来源、耗时与配置。
- 12 条开发候选题；状态全部为 candidate_review_required，参考答案尚未填写。
- 准备 RAGAS 0.4.3 的三指标评分适配器、人工评分规范、汇总工具。
- 准备依赖固定版本、环境检查、Dockerfile、Compose 和项目说明。
- 16 项本地自动检查通过：包含真实小型 Chroma 向量检索与 API/SSE 测试；模型响应使用 mock。
- 已在离线模式加载本地 BGE-M3 缓存并对一条文本完成真实向量化，输出维度为 1024；未因此进行全量建库。
- 已保存修改前源代码快照至 legacy/pre_docker_preparation；旧课程入口移入 legacy。

## 尚未完成（不能写成已取得的成果）

- 重排是否改善整体效果仍需正式对比实验。
- 真实 LLM 问答、流式网络请求和中文问答质量尚未验收。
- RAGAS 尚未安装，judge 配置与 API 评分尚未验收。
- 50+ 条经过核验的正式测试集、策略对比结果和错误案例报告尚未产生。
- 当前环境未检测到 Docker，容器文件只做配置结构检查，尚未构建或部署。
- 当前目录未初始化 Git；已准备忽略规则，后续整理发布时初始化，不自动发布。

## 下一步执行顺序

1. 已完成：核验本地 BGE-M3 与重排模型，使用语义切分建立完整索引。
2. 已完成：全量建库、ID/数量/token 检查，以及 /ready 和三个中英文检索检查。
3. 启动 API 与 Streamlit，人工验收 3～5 个 Docker 问题、来源、连续对话与上传。
4. 阅读原文，核验开发题参考答案与证据；只有核验完成的题才能设为 verified。
5. 先运行少量 verified 开发题；安装可选评测依赖，明确 JUDGE_*，小批量校准 RAGAS 与人工评分。
6. 准备并冻结至少 50 条正式测试题，比较无/有重排，之后再考虑 Top-K、切分策略。
7. 汇总结果、错误归因，再完成 Docker 本机验收、GitHub 整理和简历更新。

## 常用入口

```powershell
.\.venv\Scripts\python.exe tools/check_environment.py
.\.venv\Scripts\python.exe build_db.py --prepare-only
.\.venv\Scripts\python.exe build_db.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`artifacts/environment_check.json` 只记录配置是否存在，不包含 API Key。
`artifacts/verification_report.json` 保存本轮检查范围；`preparation_report.json` 保存数据准备统计。
当前 .env 原值未改动。D:\AI\RAG_backup 未改动。


## 最新全量建库结果

- collection：`docker_documentation`；数据库：`chroma_db_docker/`。
- 输入：53 篇正文 + 5 个支持片段，547 个解析章节。
- 切分：当前语义切分策略，字符目标 650、overlap 100；最终 1037 个 chunk。
- 模型：BGE-M3 dense；1024 维；Chroma cosine 距离。
- 全部 chunk 的 ID 与数据库记录逐项一致；最长 409 tokens，不超过配置的 512。
- collection 状态 ready，独立进程读取成功，/ready 返回 1037 条记录。
- BGE Reranker v2-m3 已在离线缓存模式下真实运行；三条中英文 smoke query 均返回相关原文。
- 中文 bridge 问题的直接对比章节出现在最终 Top-3 的第三位；不能把此检查当作排序最优或效果提升证明。
- 全过程没有调用生成 LLM 或 judge API，没有产生 RAGAS 正式分数。
- 报告：`artifacts/build_report.json`、`artifacts/index_verification_reranked.json`。
- 下一项工作：真实 LLM 问答与流式输出验收，然后人工核验开发题参考答案。
