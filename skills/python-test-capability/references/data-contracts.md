# data-contracts.md

## 1. 目的

本文件用于说明 `tests/` 当前重点保护的契约面。

---

## 2. API contract

当前重点保护：

- `/chat`
- `/chat_stream`
- `/chat_stream_cancel`
- `/chat_reset`
- `/health`

---

## 3. service / lifecycle contract

当前重点保护：

- started / delta / heartbeat / completed / error / cancelled
- completed 才进入标准 memory update
- failed / cancelled 不污染后续 request assembly

---

## 4. provider / prompt / config contract

当前重点保护：

- provider canonical result
- prompt registry / renderer
- config 与 registry 解析

---

## 5. 原则

- 保护当前已落地契约
- 已落地 retrieval / citation 必须进入测试完成态
