# acceptance-checklist.md

## 1. 目的

本文件用于在 `app/services/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### façade
- [ ] 同步 chat 入口 façade 语义清晰
- [ ] 流式 chat 入口 façade 语义清晰
- [ ] services 未重新长成主编排内核
- [ ] cancellation registry 行为清晰

### 协作
- [ ] `request_assembler` 仍是唯一装配中枢
- [ ] 与 `chat_runtime` 的调用边界清晰
- [ ] SSE 交付边界清晰

### 生命周期
- [ ] started / delta / heartbeat / completed / error / cancelled 路径清晰
- [ ] only completed assistant message 进入标准 memory update
- [ ] failed / cancelled 不污染后续 request assembly

### 边界
- [ ] 未混入 route 逻辑
- [ ] 未混入 provider SDK 细节
- [ ] 未混入 store / Redis 细节
- [ ] 未重新实现 workflow / hook / trace 主逻辑

### 回归
- [ ] 未破坏同步 chat 主链路
- [ ] 未破坏流式 chat 主链路
- [ ] 未破坏 request assembly 顺序

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格
