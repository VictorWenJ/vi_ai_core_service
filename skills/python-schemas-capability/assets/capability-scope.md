# capability-scope.md

## 1. 目的

本文件用于说明 `python-schemas-capability` 当前阶段的能力范围，避免 skill 在执行过程中发生边界漂移。

---

## 2. 当前能力范围

当前能力范围限定为：

- `LLMMessage`
- `LLMRequest`
- `LLMUsage`
- `LLMResponse`
- `LLMStreamChunk`
- 内部 canonical contract 测试

---

## 3. 当前不在范围内

当前不在范围内的能力包括：

- `/chat` request / response schema
- `/chat_stream` SSE 事件 schema
- cancel / reset contract
- citation contract
- retrieval 内部对象
- 长期记忆对象体系

---

## 4. 当前默认技术基线

- `app/schemas/` 只承载内部 `LLM*` 契约
- API 对外 schema 位于 `app/api/schemas/`
- dataclass 优先
- provider-agnostic

---

## 5. 使用原则

如果某项需求超出本文件定义的能力范围，应先更新根文档与模块 AGENTS，再更新 skill，不得在实现阶段直接越界扩展。
