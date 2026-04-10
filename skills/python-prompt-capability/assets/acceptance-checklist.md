# acceptance-checklist.md

## 1. 目的

本文件用于在 `app/prompts/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### 资产
- [ ] 模板文件清晰
- [ ] registry 清晰
- [ ] renderer 清晰

### 边界
- [ ] 未混入业务编排逻辑
- [ ] 未混入 provider transport 细节
- [ ] 未把未落地的平台化能力写成已实现事实

### 回归
- [ ] 默认 system prompt 仍可用
- [ ] registry / renderer 测试已补

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格
