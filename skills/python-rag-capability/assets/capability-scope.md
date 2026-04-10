# capability-scope.md

## 1. 目的

本文件用于说明 `python-rag-capability` 当前阶段的能力范围，避免 skill 在执行过程中发生边界漂移。

---

## 2. 当前能力范围

当前能力范围限定为：

- 文档导入
- 文档清洗
- 文档切块
- 文本 embedding
- 向量索引
- retrieval
- citation-ready 数据输出

---

## 3. 当前不在范围内

当前不在范围内的能力包括：

- 独立 RAG 微服务
- 长期记忆平台
- 审批流
- Case Workspace
- Agentic retrieval
- graph retrieval
- hybrid retrieval 大系统
- 多模态主链路
- 知识平台管理后台

---

## 4. 当前默认技术基线

- 向量数据库：Qdrant
- 相似度：Cosine
- embedding：单一文本 embedding 基线
- chunking：结构感知 + token-aware + overlap

---

## 5. 使用原则

如果某项需求超出本文件定义的能力范围，应先更新根文档与模块 AGENTS，再更新 skill，不得在实现阶段直接越界扩展。