# acceptance-checklist.md

## 1. 目的

本文件用于在 `app/rag/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### 模型
- [ ] KnowledgeDocument 已定义
- [ ] KnowledgeChunk 已定义
- [ ] RetrievedChunk 已定义
- [ ] Citation 已定义

### ingest
- [ ] parser 可用
- [ ] cleaner 行为稳定（如实现）
- [ ] chunker 使用结构感知 + token-aware + overlap
- [ ] metadata 继承正确

### embedding / index
- [ ] embedding 抽象存在
- [ ] 向量维度与索引契约一致
- [ ] index 抽象存在
- [ ] 默认基线符合当前阶段约束

### retrieval
- [ ] retrieval service 可用
- [ ] top-k 可配置
- [ ] filter 可工作
- [ ] retrieval 失败有降级

### citation
- [ ] citation 来源于 retrieval 结果
- [ ] `/chat` 可返回 citations
- [ ] `/chat_stream` completed 可返回 citations
- [ ] delta 阶段不返回 citations

### 回归
- [ ] 未破坏同步 chat 主链路
- [ ] 未破坏流式 chat 主链路
- [ ] 未破坏 Phase 4 short-term memory 语义

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格