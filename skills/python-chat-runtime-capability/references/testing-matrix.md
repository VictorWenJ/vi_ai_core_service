# testing-matrix.md

## 1. 目的

本文件用于给 `python-chat-runtime-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

### A. workflow
- step dispatch
- 顺序稳定性
- 非法 step 检测

### B. lifecycle hooks
- before_request
- after_retrieval
- before_model_call
- after_model_call
- after_stream_completed
- on_error

### C. step hooks
- before_step:* 触发
- after_step:* 触发
- mutate / block 行为

### D. sync / stream
- run_sync 正常路径
- run_stream 正常路径
- 共语义回归测试

### E. trace
- started / completed / error trace 收口
- step / hook trace 记录

### F. boundary
- request assembly 顺序未回退
- retrieval degrade 不拖垮主链路
- `/chat` 与 `/chat_stream` contract 不回退

---

## 3. 原则

- 以确定性测试为主
- 先保护当前已落地主链路
- 未落地能力不写进现有测试完成态
