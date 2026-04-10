# data-contracts.md

## 1. 目的

本文件用于说明 `app/schemas/` 中核心对象的最小契约要求。

---

## 2. LLMMessage

必须能表达：

- role
- content

并明确：
- role 只能取允许集合
- content 不能为空

---

## 3. LLMRequest

必须能表达：

- provider
- model
- messages
- system_prompt
- temperature
- max_tokens
- stream
- session_id
- conversation_id
- request_id
- metadata

---

## 4. LLMResponse / LLMUsage

必须能表达：

- content
- provider
- model
- usage
- finish_reason
- metadata
- raw_response

---

## 5. LLMStreamChunk

必须能表达：

- delta
- sequence
- finish_reason
- usage
- done
- metadata

---

## 6. 原则

- 当前不承接 `/chat`、`/chat_stream`、cancel、reset、citation 契约
- 不泄漏 provider 原始响应对象
- contract 必须稳定、可测试、可扩展
