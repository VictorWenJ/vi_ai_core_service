# testing-matrix.md

## 1. 目的

本文件用于给 `python-test-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

### A. chat
- `/chat` 正常路径
- `/chat` citations 路径
- `/chat` 降级路径

### B. stream
- started / delta / completed 顺序
- completed citations
- delta 无 citations
- error / cancelled 路径

### C. cancel / reset
- `/chat_stream_cancel`
- `/chat_reset`

### D. lifecycle
- placeholder -> completed
- placeholder -> failed
- placeholder -> cancelled
- only completed memory update

### E. assembly
- request assembly 顺序
- knowledge block 注入
- non-completed assistant message 过滤

### F. module regression
- provider canonical contract
- prompt registry / renderer
- schema contract
- context lifecycle
- retrieval / citation

---

## 3. 原则

- 以确定性测试为主
- 重点验证契约、路径、差异与降级
- 不让 tests 演化成一组不可维护的脆弱脚本