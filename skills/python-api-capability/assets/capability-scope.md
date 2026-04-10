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
- API 层 request / response schema
- SSE 事件格式化
- API 错误映射
- API 层 HTTP / 集成测试

---

## 3. 当前不在范围内

当前不在范围内的能力包括：

- chat 主链路编排
- assistant message lifecycle 实现
- context memory 实现
- retrieval / chunking / embedding / index 实现
- provider 主链路实现
- citation 生成逻辑
- 长期记忆平台
- 审批流
- Case Workspace

---

## 4. 当前默认技术基线

- 框架：FastAPI
- 流式协议：SSE
- `/chat_stream`：`text/event-stream`
- `/chat_stream_cancel`：显式取消入口
- `/chat_reset`：上下文重置入口
- `/chat`：支持 citations
- `/chat_stream`：仅 completed 事件支持 citations

---

## 5. 使用原则

如果某项需求超出本文件定义的能力范围，应先更新根文档与模块 AGENTS，再更新 skill，不得在实现阶段直接越界扩展。