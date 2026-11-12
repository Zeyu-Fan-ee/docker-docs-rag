# 公开展示说明

## 项目评测摘要

- 语料：固定版本的 Docker 官方公开文档，模拟技术支持文档问答。
- 题集：104 道经核验的问题，包括 93 道可回答题和 11 道证据不足题。参考答案和证据见 `evaluation/datasets/test104_verified_v1.jsonl`。
- 配置：BGE-M3 向量检索 Top-10，BGE 重排后取 Top-3，DeepSeek Flash 生成；RAGAS 0.4.3 使用 Qwen-Plus 评分。
- 93 道可回答题的单次模型评分：Faithfulness 0.885、Factual Correctness 0.568、Context Recall 0.971。11 道证据不足题不计入这三项均值，另行核查。
- 评分受到 Judge 与参考答案影响，不等同于人工准确率。原 0.240 来自另一批答案和另一 Judge，不能据此计算系统效果提升。完整方法和核查见 `evaluation/reports/test104_qwen_review_v1.md`。

原始生成答案及逐条评分位于本机 `evaluation/results/`，默认由 `.gitignore` 排除；历史报告可能引用这些本地文件，公开仓库中这些链接不会提供相应文件。

## 拟公开内容

- 主程序、API、页面、Docker 配置、依赖清单和测试代码。
- Docker 官方文档语料、来源清单及其上游许可证。
- `evaluation/datasets/` 测试数据、`evaluation/reports/` 评测报告、项目架构及运行说明。
- `.env.example` 配置模板，不包含真实密钥。

## 默认不公开

`.env` 和 `.env.*`（模板 `.env.example` 除外）、虚拟环境、本地及容器数据库、上传文件、`artifacts/`、`evaluation/results/` 原始运行结果、`legacy/` 历史快照和缓存。容器数据卷位于 Docker 环境中，也不随项目目录上传。

首次创建提交前仍需审查实际暂存文件、密钥、数据来源及许可证。当前项目尚未建立 Git 仓库，也尚未选择仓库的公开或私有设置。
