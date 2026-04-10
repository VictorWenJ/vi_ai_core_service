# capability-scope.md

## 1. 目的

本文件用于说明 `python-api-capability` 当前阶段的能力范围，避免 skill 在执行过程中发生边界漂移。

---

## 2. 当前能力范围

当前能力范围限定为：

- `/chat`
- `/chat_stream`
- `/chat_stream_cancel`
- `/chat_reset`
- `/health`
- API schema
- SSE 文本序列化
- API 测试

---

## 3. 当前不在范围内

当前不在范围内的能力包括：

- chat 主链路编排
- context memory
- provider SDK 调用
- retrieval / chunking / embedding / index
- citation 生成
- 长期记忆平台
- 审批流
- Case Workspace

---

## 4. 当前默认技术基线

- FastAPI
- SSE
- `/chat_stream` 返回 `text/event-stream`
- 当前不包含 citations

---

## 5. 使用原则

如果某项需求超出本文件定义的能力范围，应先更新根文档与模块 AGENTS，再更新 skill，不得在实现阶段直接越界扩展。
