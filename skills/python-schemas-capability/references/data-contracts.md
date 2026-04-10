# data-contracts.md

## 1. 目的

本文件用于说明 `app/schemas/` 中关键 contract 的最小要求。

---

## 2. chat contract

必须能表达：

- 用户输入
- 会话标识
- provider / model（如当前项目支持）
- answer
- usage / finish_reason（如当前项目支持）
- citations（Phase 6）

---

## 3. stream event contract

至少应能表达：

- `response.started`
- `response.delta`
- `response.completed`
- `response.error`
- `response.cancelled`
- `response.heartbeat`

并满足：

- completed 可带 citations
- delta 不带 citations

---

## 4. cancel / reset contract

必须能表达：

- cancel：取消目标信息与取消结果
- reset：session / conversation 重置语义与结果

---

## 5. lifecycle / citation contract

必须能表达：

- lifecycle 字段的共享语义
- citation 的展示语义
- citation 来源可追溯但不透传内部对象

---

## 6. 原则

- 共享 contract 不应等于内部对象直透
- 命名必须稳定
- 语义必须一致
- 应尽量兼容已有主链路