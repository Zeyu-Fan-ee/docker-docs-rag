# Docker 技术文档 RAG 问答系统

面向企业开发与运维的容器技术支持场景，使用 Docker 官方公开文档构建可溯源问答原型。
这是可复用的文档问答工程，不代表已在真实企业部署，也不保证消除幻觉。

## 当前入口

| 模块 | 文件 | 作用 |
|---|---|---|
| 配置 | project_config.py | 统一路径、模型、切分与检索参数 |
| 解析 | document_processor.py | MD/TXT/PDF/DOCX，标题、代码、表格、来源与行号 |
| 切分与入库 | ingestion.py、semantic_chunker.py、build_db.py | 共享切分、稳定 ID、token 长度保护、索引指纹 |
| 检索 | vector_store.py、retriever.py | Chroma dense 召回、可选 BGE 重排、完整轨迹 |
| 生成 | rag_pipeline.py | 多轮改写、证据约束、普通/流式生成 |
| 服务 | api.py | /health、/ready、/chat、/chat/stream、/upload |
| 界面 | streamlit_app.py | 对话、来源 URL、上传、知识库状态 |
| 评测 | evaluation/ | 测试题校验、逐题运行、可选 RAGAS 评分 |
| 历史 | legacy/ | 本机旧入口与修改前快照，不属于当前运行链，也不纳入公开仓库 |

## 本地运行

推荐 Python 3.13。以下命令都在项目根目录执行；新环境需要先创建虚拟环境。
新环境安装 `requirements.txt`；它固定直接依赖，`requirements.lock.txt` 是当前环境的已安装版本快照，尚未跨平台验证。
首次运行时将 `.env.example` 复制为 `.env`，再在本机填写模型配置与 API 密钥；不要公开 `.env`。

```powershell
.\.venv\Scripts\python.exe build_db.py --prepare-only
# 完整建库会加载/可能下载 BGE-M3；默认语义切分在 CPU 上较慢。
.\.venv\Scripts\python.exe build_db.py
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000 --workers 1
# 另一个终端
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

`/health` 仅证明服务存活；`/ready` 检查索引存在、完整且配置匹配，不提前加载生成或重排模型。
重排模型第一次使用可能需要下载。没有模型或 API 时，服务仍能启动，但问答不能算验收通过。
本地路径以项目根目录为基准，不依赖启动终端所在位置。

## 数据与索引

`data/docker_official/manifest.json` 固定官方 commit，记录原文 URL、哈希和主题；LICENSE 为上游 Apache-2.0。
`dependencies.json` 记录同版本 include、功能版本摘要与配置；包含片段作为独立来源解析，原文不改写。
Markdown 导航空页会被排除；站点模板不能解析时，完整建库拒绝继续，详见准备报告。
功能摘要转成文本，命令代码中的 Go 模板保留；本地 PDF 没有 OCR，复杂图表仍需人工核验。

只读取 manifest 列出的正文与指定 include；README、测试答案、历史资料不进入知识库。
`build_db.py --prepare-only` 生成 `artifacts/parsed_sections.jsonl` 与 `preparation_report.json`，不加载模型、不调用 API。
完整建库生成 `chunks.jsonl` 与 `build_report.json`；实际 chunk 将再次检查 tokenizer 长度，避免向量化静默截断。
chunk 来源行号指向原始章节范围，不声称是单个 chunk 的精确起止行。

建库不覆盖已存在 collection。切分/模型/解析实现改变时，设置新的 `COLLECTION_NAME` 后重建，并重启服务。
失败的构建标记 failed，不用于问答；不能把仅解析成功当作已建库。
上传与离线构建共用处理逻辑；上传会改变实验语料，正式评测时禁止上传。

## 评测与边界

见 `evaluation/README.md`。已整理并核验 104 道测试题，覆盖可回答题及证据不足题；题目与参考依据记录在 `evaluation/datasets/test104_verified_v1.jsonl`。
默认比较 dense Top-10→Top-3 与同一召回预算下重排 Top-3。BM25/Hybrid 尚未实现。
RAGAS 是主要评测框架；Factual Correctness、Faithfulness、Context Recall 分别评价正确性、依据性和证据覆盖。
104 题中 93 道可回答题使用 DeepSeek Flash 生成、Qwen-Plus 作为 Judge 进行单次 RAGAS 评分：Faithfulness 0.885、Factual Correctness 0.568、Context Recall 0.971；11 道证据不足题单独核查。范围与方法见 `evaluation/reports/test104_qwen_review_v1.md`。这些是模型评分，不等同于真实正确率；旧的 0.240 使用不同答案及 Judge，不可直接视为系统效果提升。
公开范围及原始记录说明见 `docs/PUBLICATION.md`；原始逐题生成和评分文件默认不纳入仓库。
会话仅存在进程内；限制单进程 demo 使用，尚无企业权限控制与持久化会话。

## Docker 本机部署

```powershell
docker compose build
docker compose run --rm -e ARTIFACT_DIR=/app/runtime/docker-build-artifacts api python build_db.py
docker compose up -d
```

容器索引和本地索引独立，模型缓存与运行数据用命名卷保存。镜像不复制 `.env`、本地向量库、历史文件或上传资料。
首次建库需要下载模型且可能耗时；已有容器知识库时不需要重新建库。本机已构建并启动 API 与页面，用户已实际提问并收到回答。页面为 http://127.0.0.1:8501，操作与排查见 `docs/DOCKER_GUIDE.md`。

## 检查

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

自动检查使用伪造的模型响应和小型临时数据，验证软件契约，不代表真实模型问答质量。
架构说明见 `docs/ARCHITECTURE.md`；`docs/STATUS.md` 保留早期工作记录。

架构相关实现依据：[Chroma collection 配置](https://docs.trychroma.com/docs/collections/configure)、
[RAGAS 0.4.3 指标导出](https://github.com/vibrantlabsai/ragas/blob/v0.4.3/src/ragas/metrics/collections/__init__.py)。
