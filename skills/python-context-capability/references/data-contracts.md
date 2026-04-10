# data-contracts.md

## 1. 目的

本文件用于说明 `app/context/` 中核心数据对象的最小契约要求。

---

## 2. ContextWindow

必须能表达：

- session_id
- conversation_id
- recent raw messages
- rolling summary
- working memory
- runtime_meta

并明确：
- `messages` 仅表示 recent raw messages

---

## 3. ContextMessage

必须能表达：

- message_id
- role
- content
- status
- created_at
- updated_at
- finish_reason
- error_code
- metadata

---

## 4. RollingSummaryState

必须能表达：

- summary text
- 更新时间
- 来源范围或统计信息（如当前实现支持）

---

## 5. WorkingMemoryState

必须能表达：

- active_goal
- constraints
- decisions
- open_questions
- next_step
- 更新时间

---

## 6. 原则

- external knowledge 不属于 context model
- citations 不属于 context model
- lifecycle 字段必须可序列化、可持久化、可回归测试