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
- completed citations 输出，delta 不输出 citations

### C. cancel / reset / health
- `/chat_stream_cancel`
- `/chat_reset`
- `/health`

### D. integration
- HTTP smoke

### E. Phase 6
- `/chat` citations 输出与空数组测试
- retrieval 失败时 chat/stream 仍成功测试

---

## 3. 原则

- 以确定性测试为主
- 先保护当前已落地 API 契约
- citations 契约变更必须同步测试
