# capability-scope.md

## 1. 目的

本文件用于说明 `python-rag-capability` 当前阶段的能力范围，避免 skill 在执行过程中发生边界漂移。

---

## 2. 当前能力范围

当前能力范围限定为：

- `app/rag/` 运行时代码的首次落地
- 知识对象模型
- ingest pipeline
- retrieval service
- citation 结构
- RAG 相关测试

---

## 3. 当前不在范围内

当前不在范围内的能力包括：

- API 路由
- chat 主链路编排
- short-term memory
- provider chat completion
- 长期记忆平台
- 审批流
- Case Workspace
- Agent Runtime
- 多模态主链路

---

## 4. 当前默认技术基线

- 当前代码已有 RAG 运行时代码
- 默认向量库：Qdrant
- 默认相似度：Cosine
- 默认 chunking：结构感知 + token-aware + overlap
- 默认 citation：来自 retrieval 结果

---

## 5. 使用原则

如果某项需求超出本文件定义的能力范围，应先更新根文档与模块 AGENTS，再更新 skill，不得在实现阶段直接越界扩展。
