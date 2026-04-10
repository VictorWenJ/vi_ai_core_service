# testing-matrix.md

## 1. 目的

本文件用于给 `python-test-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

### A. api
- `/chat`
- `/chat_stream`
- `/chat_stream_cancel`
- `/chat_reset`
- `/health`

### B. context
- manager
- policy pipeline
- store / factory
- memory reducer

### C. services
- sync chat
- stream lifecycle
- request assembly

### D. provider / prompt / config
- provider normalization
- prompt service
- config

### E. integration
- HTTP smoke

### F. future Phase 6
- 若后续实现 retrieval / citation，再补对应测试矩阵

---

## 3. 原则

- 以确定性测试为主
- 先保护当前已落地测试面
- 不把未落地能力写进现有完成态
