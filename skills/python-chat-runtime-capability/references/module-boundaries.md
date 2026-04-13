# module-boundaries.md

## 1. 目的

本文件用于说明 `app/chat_runtime/` 与其他模块之间的边界关系。

---

## 2. 与 services 的边界

### chat_runtime 负责
- workflow / hook / trace 主执行语义
- sync / stream 共语义收口

### services 负责
- 外部请求入口 façade
- 结果交付
- SSE 协作

---

## 3. 与 context 的边界

### chat_runtime 负责
- 决定何时触发 memory 收口

### context 负责
- 状态模型
- layered memory
- store / policy / codec

---

## 4. 与 prompts / request_assembler 的边界

chat runtime 不重新定义装配顺序；
`ChatRequestAssembler` 仍是唯一装配中枢。

---

## 5. 与 providers 的边界

chat runtime 决定何时调用 provider；
providers 负责厂商适配与 canonical result。

---

## 6. 与 rag 的边界

chat runtime 负责编排 retrieval；
rag 负责知识实现与 citations 生成。

---

## 7. 结论

`app/chat_runtime/` 是聊天执行骨架层，不是协议层、不是 SDK 层、不是知识实现层，也不是当前阶段的 Agent 平台层。
