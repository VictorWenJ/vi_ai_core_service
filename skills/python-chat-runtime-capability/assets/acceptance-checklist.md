# acceptance-checklist.md

## 1. 目的

本文件用于在 `app/chat_runtime/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### workflow
- [ ] 主 workflow 已显式存在
- [ ] 主 workflow 只包含主步骤
- [ ] workflow 顺序清晰、可追踪

### hook
- [ ] lifecycle hook 已显式存在
- [ ] step hook 已显式存在
- [ ] hook 未与主 workflow 混在一起
- [ ] hook 只承担 lifecycle control

### 执行语义
- [ ] sync / stream 共用同一套主语义
- [ ] request assembly 仍通过唯一中枢完成
- [ ] trace 已统一收口

### 边界
- [ ] 未混入 HTTP / SSE 文本协议
- [ ] 未混入 provider SDK 细节
- [ ] 未越界实现 Tool / Agent / runtime skill loader

### 回归
- [ ] 未破坏 `/chat` contract
- [ ] 未破坏 `/chat_stream` contract
- [ ] 未破坏 citations 行为

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格
