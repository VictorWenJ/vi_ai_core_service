# acceptance-checklist.md

## 1. 目的

本文件用于在 `app/schemas/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### 模型
- [ ] `LLMMessage` 语义清晰
- [ ] `LLMRequest` 语义清晰
- [ ] `LLMUsage` 语义清晰
- [ ] `LLMResponse` 语义清晰
- [ ] `LLMStreamChunk` 语义清晰

### 校验
- [ ] role 校验清晰
- [ ] temperature / max_tokens 校验清晰
- [ ] 字段归一化行为稳定

### 边界
- [ ] 未混入 API 对外 schema
- [ ] 未混入 retrieval / citation 对象
- [ ] 未泄漏 provider 原始 SDK 对象

### 回归
- [ ] 未破坏 service / provider 既有调用
- [ ] 未破坏流式与非流式语义一致性

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格
