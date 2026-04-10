# acceptance-checklist.md

## 1. 目的

本文件用于在 `app/context/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### 模型
- [ ] `ContextWindow` 语义清晰
- [ ] `ContextMessage` 语义清晰
- [ ] `RollingSummaryState` 语义清晰
- [ ] `WorkingMemoryState` 语义清晰

### 生命周期
- [ ] lifecycle 字段完整
- [ ] placeholder 可创建
- [ ] completed 可 finalize
- [ ] failed / cancelled 可收口
- [ ] only completed assistant message 进入标准 memory update

### store
- [ ] store contract 清晰
- [ ] codec 序列化稳定
- [ ] redis / in-memory 行为一致

### 边界
- [ ] retrieval 语义未混入 context
- [ ] citations 语义未混入 context
- [ ] `ContextWindow.messages` 仍只表示 recent raw

### 回归
- [ ] 未破坏 Phase 2 policy pipeline
- [ ] 未破坏 Phase 4 layered memory
- [ ] 未破坏 Phase 5 streaming lifecycle 兼容性

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格