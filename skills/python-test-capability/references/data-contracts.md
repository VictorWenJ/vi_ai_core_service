# data-contracts.md

## 1. 目的

本文件用于说明 tests 层重点关注的共享契约与关键行为边界。

---

## 2. chat / stream contract

tests 至少应关注：

- `/chat` request / response
- `/chat_stream` event 序列
- `/chat_stream_cancel`
- `/chat_reset`

---

## 3. lifecycle contract

tests 至少应关注：

- created / streaming / completed / failed / cancelled
- only completed 进入标准 memory update
- non-completed assistant message 不参与后续装配

---

## 4. retrieval / citation contract

tests 至少应关注：

- `/chat` citations
- `/chat_stream` completed citations
- delta 无 citations
- retrieval 失败降级

---

## 5. 原则

tests 关注的是：
- contract 稳定性
- 行为边界
- 路径差异

不是内部实现细节逐行镜像。