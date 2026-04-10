# module-boundaries.md

## 1. 目的

本文件用于说明 `app/rag/` 与其他模块之间的边界关系。

---

## 2. 与 services 的边界

### rag 负责
- ingest
- chunk
- embed
- index
- retrieve
- citation-ready 数据

### services 负责
- retrieval 时机
- request assembly 时机
- citations 进入响应的时机
- chat / stream 主链路编排

---

## 3. 与 context 的边界

### context 负责
- recent raw
- rolling summary
- working memory
- message lifecycle 状态

### rag 负责
- 外部知识对象
- 文档切块
- 向量检索
- citations

### 原则
retrieval 结果不是 working memory，  
citation 不是 rolling summary。

---

## 4. 与 providers 的边界

### providers 负责
- embedding provider 抽象与实现
- chat provider 抽象与实现

### rag 负责
- 使用 embedding 能力完成向量化
- 不负责 chat provider 主链路

---

## 5. 与 api / schemas 的边界

### rag 不负责
- HTTP 协议
- SSE 事件序列化
- 最终外部响应封装

### rag 负责
- 为 citations 提供稳定内部数据来源

---

## 6. 结论

`app/rag/` 是知识增强实现域，不是 chat 编排域，也不是 short-term memory 域，更不是独立产品平台。