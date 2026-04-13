# testing-matrix.md

## 1. 目的

本文件用于给 `python-service-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

### A. sync façade
- runtime request 映射
- 同步结果返回
- provider / config 错误路径

### B. stream façade
- started / delta / heartbeat / completed 路径
- cancel / timeout / error 路径
- SSE 交付兼容性

### C. request assembly
- system / knowledge / working memory / rolling summary / recent raw / user 顺序
- non-completed assistant message 过滤
- context_assembly trace

### D. compatibility
- 已落地 Phase 2~7 行为不回退
- API 调用 services 的入口保持稳定

### E. current phase
- services 通过 chat runtime 执行测试
- 未重新形成双编排内核测试

---

## 3. 原则

- 以确定性测试为主
- 先保护当前已落地主链路
- 未落地能力不写进现有测试完成态
