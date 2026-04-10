# testing-matrix.md

## 1. 目的

本文件用于给 `python-service-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

### A. sync chat
- 默认 provider / model 解析
- system prompt 注入
- context completed 收口
- provider / config 错误路径

### B. stream chat
- started / delta / heartbeat / completed 路径
- cancel / timeout / error 路径
- placeholder / finalize 收口

### C. request assembly
- system / working memory / rolling summary / recent raw / user 顺序
- non-completed assistant message 过滤
- context_assembly trace

### D. compatibility
- 已落地 Phase 2~5 行为不回退
- API 调用 services 的入口保持稳定

### E. future Phase 6
- 若后续新增 retrieval / citations，再追加对应编排测试

---

## 3. 原则

- 以确定性测试为主
- 先保护当前已落地主链路
- 未落地能力不写进现有测试完成态
