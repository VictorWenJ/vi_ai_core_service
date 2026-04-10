# data-contracts.md

## 1. 目的

本文件用于说明 `app/providers/` 中核心对象的最小契约要求。

---

## 2. chat completion contract

必须能表达：

- text / content
- finish_reason
- usage
- model
- provider
- metadata（如当前实现需要）

---

## 3. stream chunk contract

必须能表达：

- delta
- sequence（如当前实现需要）
- finish_reason（结束时）
- usage（结束时，如当前实现支持）
- error 信息（异常路径）

---

## 4. embedding contract

必须能表达：

- vectors
- model
- dimension
- data type（float 语义）
- batch 行为

---

## 5. 原则

- 不直接透传厂商原始响应
- 上层只消费 canonical contract
- contract 必须稳定、可测试、可扩展