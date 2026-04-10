# module-boundaries.md

## 1. 目的

本文件用于说明 `app/providers/` 与其他模块之间的边界关系。

---

## 2. 与 services 的边界

### providers 负责
- 调用厂商
- 输出 canonical result
- 映射错误
- 提供 embedding

### services 负责
- chat / stream 编排
- lifecycle 推进
- cancel / reset / retrieval 时机
- citations 输出时机

---

## 3. 与 api 的边界

API 不直接调用 provider SDK。  
provider 通过 service 间接服务于 API。

---

## 4. 与 context 的边界

context 负责会话状态；providers 不直接操作 context。  
providers 只提供模型能力。

---

## 5. 与 rag 的边界

rag 负责 retrieval / citation-ready 数据。  
providers 可提供 embedding，但不负责 retrieval / citation。

---

## 6. 结论

`app/providers/` 是模型与厂商接入层，不是业务编排层，不是知识检索层，也不是上下文状态层。