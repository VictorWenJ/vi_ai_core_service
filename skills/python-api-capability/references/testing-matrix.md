# testing-matrix.md

## 1. 目的

本文件用于给 `python-api-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

### A. chat
- `/chat` 正常路径
- error mapping

### B. stream
- started / delta / completed 事件
- error / cancelled / heartbeat 路径

### C. cancel / reset / health
- `/chat_stream_cancel`
- `/chat_reset`
- `/health`

### D. integration
- HTTP smoke

### E. future Phase 6
- 若后续真实新增 citations，再补对应输出测试

---

## 3. 原则

- 以确定性测试为主
- 先保护当前已落地 API 契约
- 不把未落地 citations 写进现有测试完成态
