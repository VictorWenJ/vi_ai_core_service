# acceptance-checklist.md

## 1. 目的

本文件用于在 `app/providers/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### 抽象
- [ ] chat completion 抽象清晰
- [ ] stream completion 抽象清晰
- [ ] embedding 抽象清晰

### contract
- [ ] non-stream canonical response 稳定
- [ ] stream canonical chunk 稳定
- [ ] embedding 输出结构稳定
- [ ] finish / usage / error 映射清晰

### 边界
- [ ] 未混入业务编排
- [ ] 未混入 retrieval / citation
- [ ] 未直接操作 context state
- [ ] 未直接承担 API 职责

### 当前阶段约束
- [ ] embedding 已纳入 provider 域
- [ ] 仅文本 embedding 为主
- [ ] 未引入重复 provider skill 体系

### 回归
- [ ] 未破坏同步 chat 主链路
- [ ] 未破坏流式 chat 主链路
- [ ] 未破坏 retrieval 对 embedding 的接入需求

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格