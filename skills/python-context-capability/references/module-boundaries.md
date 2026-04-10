# module-boundaries.md

## 1. 目的

本文件用于说明 `app/context/` 与其他模块之间的边界关系。

---

## 2. 与 services 的边界

### context 负责
- state
- lifecycle 字段
- layered memory
- completed 态 memory update

### services 负责
- chat / stream 主链路编排
- retrieval 调度
- cancel / timeout 收口
- request assembly 调用时机

---

## 3. 与 api 的边界

API 不直接操作 context manager。  
上下文读取、更新、重置都应通过 service 触发。

---

## 4. 与 rag 的边界

### context 负责
- short-term memory
- recent raw / rolling summary / working memory

### rag 负责
- external knowledge grounding
- retrieval
- citation-ready 数据

### 原则
retrieval 结果不是 working memory，  
citation 不是 rolling summary。

---

## 5. 与 providers 的边界

provider 负责模型厂商接入与 canonical result。  
context 不直接依赖 provider SDK。

---

## 6. 结论

`app/context/` 是会话短期状态层，不是业务编排层，不是知识增强层，也不是长期记忆平台。