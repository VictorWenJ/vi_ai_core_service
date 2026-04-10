# acceptance-checklist.md

## 1. 目的

本文件用于在 `app/observability/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### 核心能力
- [ ] `log_report` 行为清晰
- [ ] JSON-safe 序列化行为清晰
- [ ] stdout logger 初始化稳定

### 边界
- [ ] 未混入业务编排逻辑
- [ ] 未混入状态存储语义
- [ ] 未把未落地 retrieval / citation 字段写成现有能力

### 回归
- [ ] 未破坏同步主链路
- [ ] 未破坏流式主链路
- [ ] 已补对应测试

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格
