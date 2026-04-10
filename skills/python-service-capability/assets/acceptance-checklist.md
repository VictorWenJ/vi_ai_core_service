# acceptance-checklist.md

## 1. 目的

本文件用于在 `app/services/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### 编排
- [ ] 同步 chat 编排语义清晰
- [ ] 流式 chat 编排语义清晰
- [ ] cancellation registry 行为清晰
- [ ] request_assembler 仍是唯一装配中枢

### 生命周期
- [ ] started / delta / heartbeat / completed / error / cancelled 路径清晰
- [ ] only completed assistant message 进入标准 memory update
- [ ] failed / cancelled 不污染后续 request assembly

### 边界
- [ ] 未混入 route 逻辑
- [ ] 未混入 provider SDK 细节
- [ ] 未混入 store / Redis 细节
- [ ] retrieval / citations 保持 services 编排边界，未侵入 API/provider/context

### 回归
- [ ] 未破坏同步 chat 主链路
- [ ] 未破坏流式 chat 主链路
- [ ] 未破坏 request assembly 顺序

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格
