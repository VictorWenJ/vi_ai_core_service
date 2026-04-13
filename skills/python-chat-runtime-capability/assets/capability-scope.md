# capability-scope.md

## 1. 目的

本文件用于说明 `python-chat-runtime-capability` 当前阶段的能力范围，避免 skill 在执行过程中发生边界漂移。

---

## 2. 当前能力范围

当前能力范围限定为：

- workflow 主数组
- lifecycle hooks
- step hooks
- sync / stream 共语义执行
- trace 收口
- runtime 模型
- skills 引用位预留
- runtime 相关测试

---

## 3. 当前不在范围内

当前不在范围内的能力包括：

- HTTP 路由与 SSE 文本协议
- provider SDK 适配
- context store 底层实现
- rag 子域内部 parser / chunker / embedding / index 细节
- Tool Calling Runtime
- Agent Runtime / Planner / Executor
- runtime skill loader
- 前端适配

---

## 4. 当前默认技术基线

- 模块目录：`app/chat_runtime/`
- 主流程：数组配置
- hook：事件数组配置 + step 前后事件数组配置
- skill：引用位预留
- sync / stream：共语义，不共交付

---

## 5. 使用原则

如果某项需求超出本文件定义的能力范围，应先更新根文档与模块 AGENTS，再更新 skill，不得在实现阶段直接越界扩展。
