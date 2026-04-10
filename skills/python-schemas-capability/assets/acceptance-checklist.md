# acceptance-checklist.md

## 1. 目的

本文件用于在 `app/schemas/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### request / response
- [ ] `/chat` request schema 清晰
- [ ] `/chat` response schema 清晰
- [ ] 命名稳定、语义明确

### stream
- [ ] `/chat_stream` 事件 schema 清晰
- [ ] started / delta / completed / error / cancelled / heartbeat 语义明确
- [ ] completed 可带 citations
- [ ] delta 不带 citations

### cancel / reset
- [ ] `/chat_stream_cancel` contract 清晰
- [ ] `/chat_reset` contract 清晰

### lifecycle / citation
- [ ] lifecycle 字段语义清晰
- [ ] citation 结构清晰、可展示
- [ ] citation 不是内部 retrieval 对象透传

### 边界
- [ ] schemas 仍只是共享契约层
- [ ] 未混入业务逻辑
- [ ] 未泄漏 provider / rag / context 内部实现细节

### 回归
- [ ] 未破坏已有主链路 contract
- [ ] 与同步 / 流式主链路兼容

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格