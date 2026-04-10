# capability-scope.md

## 1. 目的

本文件用于说明 `python-service-capability` 当前阶段的能力范围，避免 skill 在执行过程中发生边界漂移。

---

## 2. 当前能力范围

当前能力范围限定为：

- 同步 chat 编排
- 流式 chat 编排
- request assembly
- cancellation registry
- assistant message lifecycle 收口
- retrieval orchestration
- citations 输出编排
- service 级错误收敛
- service 相关测试

---

## 3. 当前不在范围内

当前不在范围内的能力包括：

- HTTP 路由与 SSE 文本协议
- provider SDK 适配
- context store 底层实现
- Prompt 模板资产治理
- retrieval / chunking / embedding / index 运行时代码
- citation 生成逻辑（由 rag 子域负责）
- 长期记忆平台
- 审批流
- Case Workspace
- Agent Runtime

---

## 4. 当前默认技术基线

- 同步入口：`ChatService` / `LLMService`
- 流式入口：`StreamingChatService`
- 装配中枢：`ChatRequestAssembler`
- 取消协调：`CancellationRegistry`
- 当前装配顺序：system -> knowledge -> working memory -> rolling summary -> recent raw -> user
- 当前已包含 retrieval / citations 编排

---

## 5. 使用原则

如果某项需求超出本文件定义的能力范围，应先更新根文档与模块 AGENTS，再更新 skill，不得在实现阶段直接越界扩展。
