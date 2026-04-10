# acceptance-checklist.md

## 1. 目的

本文件用于在 `app/api/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### 接入
- [ ] `/chat` 路径清晰
- [ ] `/chat_stream` 路径清晰
- [ ] `/chat_stream_cancel` 路径清晰
- [ ] `/chat_reset` 路径清晰
- [ ] `/health` 路径清晰

### 契约
- [ ] API schema 清晰
- [ ] SSE 事件稳定
- [ ] error mapping 清晰

### 边界
- [ ] 未混入业务编排
- [ ] 未混入 retrieval / provider SDK 逻辑
- [ ] citations 字段仅作为 schema 契约透传

### 回归
- [ ] 已补对应测试
- [ ] HTTP 集成路径稳定

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格
