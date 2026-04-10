# acceptance-checklist.md

## 1. 目的

本文件用于在 `app/providers/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### 抽象
- [ ] provider 抽象清晰
- [ ] canonical response / chunk 清晰
- [ ] registry / maturity 清晰

### 行为
- [ ] implemented provider 行为稳定
- [ ] scaffolded provider 行为稳定
- [ ] 错误映射合理

### 边界
- [ ] 未混入业务编排
- [ ] 未混入 retrieval / citation
- [ ] 未把未落地 embedding 写成已实现事实

### 回归
- [ ] 未破坏同步调用
- [ ] 未破坏流式调用
- [ ] 已补对应测试

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格
