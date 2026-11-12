# 架构与实验边界

```mermaid
flowchart TD
  A[固定版本 Docker 原文与依赖] --> B[文档解析与来源位置]
  B --> C[清洗章节与准备报告]
  C --> D[语义或递归切分]
  D --> E[token 上限检查与稳定 ID]
  E --> F[BGE-M3 dense 向量]
  F --> G[Chroma 独立 collection]
  U[用户问题与最近历史] --> Q[可选多轮改写]
  Q --> R[Top-K 召回]
  G --> R
  R --> S[可选 BGE 重排]
  S --> T[最终上下文与引用映射]
  T --> L[LLM API 依据上下文生成]
  L --> UI[FastAPI SSE 与 Streamlit]
  R --> TRACE[离线运行轨迹]
  S --> TRACE
  L --> TRACE
  GOLD[人工验证的问题与参考证据] --> EVAL[RAGAS 与人工复核]
  TRACE --> EVAL
```

解析层不加载模型；服务启动不自动创建空知识库、不在导入时调用 LLM。
索引保存处理配置指纹与 ready/failed 状态，阻止不同切分/模型混用。
来源依据为原文 URL 与章节行号；include 内容保留独立来源，功能版本条件来自同 commit 的元数据。
重排无法补回召回阶段遗漏的证据；context 相关不代表答案正确，生成和检索分开评价。

当前范围是 dense 检索、cross-encoder 重排与文档问答。权限隔离、混合检索、OCR、模型微调、生产并发不在当前已完成能力中。
