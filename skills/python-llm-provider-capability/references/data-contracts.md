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
- metadata

---

## 3. stream chunk contract

必须能表达：

- delta
- sequence
- finish_reason
- usage
- done
- metadata

---

## 4. 原则

- 不直接透传厂商原始响应
- 上层只消费 canonical contract
- embedding 通过独立 contract（`BaseEmbeddingProvider` / `EmbeddingResult`）表达
