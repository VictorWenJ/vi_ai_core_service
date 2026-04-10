# app/services/AGENTS.md

> 更新日期：2026-04-10

## 1. 文档定位

本文件定义 `app/services/` 的职责、边界、结构约束与 review 标准。  
当前阶段，本文件临时同时承担该模块的 AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW 职责。

---

## 2. 模块定位

`app/services/` 是系统的应用编排层。  
它负责把 API 层与 context / prompts / rag / providers 串成完整业务链路。

当前阶段建议围绕以下职责组织：

- `chat_service.py`：同步聊天主链路
- `request_assembler.py`：统一请求装配入口
- `streaming_chat_service.py`：流式聊天编排入口
- `cancellation_registry.py`：运行时取消协调
- 检索增强与 citation 装配相关 service / helper（本轮允许新增）

---

## 3. 本层职责

1. 承接同步与流式两类会话用例
2. 协调 context / prompts / rag / providers
3. 管理 assistant message 生命周期
4. 管理 started / delta / completed / error / cancelled 收口
5. 在 completed 时触发 Phase 4 的 layered memory 标准更新
6. 管理 cancel / timeout / failure 的业务编排
7. 在 Phase 6 中协调 retrieval、knowledge block 注入与 citations 输出

---

## 4. 本层不负责什么

1. 不负责 HTTP 路由
2. 不负责 provider SDK / HTTP 适配细节
3. 不负责 context store 的底层存储实现
4. 不负责定义共享数据契约本身
5. 不负责 SSE 文本协议
6. 不负责把 summary / reducer 算法写死在 service 里
7. 不负责 parser / chunker / embedding / vector index 的底层实现

---

## 5. 依赖边界

### 允许依赖
- `app/context/`
- `app/prompts/`
- `app/rag/`
- `app/providers/`
- `app/schemas/`
- `app/observability/`

### 禁止依赖
- `app/api/`
- Redis client、key 拼接、TTL 细节
- 向量库底层 SDK 作为常规业务编排路径直接散落在 service 层

---

## 6. 架构原则

### 6.1 编排优先，细节下沉
services 负责“编排”，不负责“底层实现”。

### 6.2 request_assembler 是上下文与知识装配中枢
assembler 是唯一允许决定以下顺序的地方：

1. system prompt
2. working memory block
3. rolling summary block
4. retrieved knowledge block
5. recent raw messages
6. current user input

### 6.3 生命周期调度必须收敛在 services
API 不负责状态机；context 不负责流式业务编排；providers 不负责外部会话生命周期；rag 不负责 chat 主链路编排。

### 6.4 completed 收口必须与 Phase 4 对齐
- completed：执行标准 `update_after_chat_turn` / `update_after_stream_completion`
- failed / cancelled：只更新消息状态，不走标准 memory update
- delta：只负责传输与聚合，不写 rolling summary / working memory

### 6.5 retrieval 是增强链路，不是主链路替代
- retrieval 结果用于知识 grounding
- retrieval 不替代 Phase 4 的 short-term memory
- retrieval 失败时，services 必须支持可控降级，不拖垮主 chat 链路

---

## 7. 当前阶段能力声明

当前本轮必须落地：

- Knowledge + Citation Layer 的 service 侧编排接入
- retrieval query 构建与 retrieval 调用入口
- request_assembler 注入 retrieved knowledge block
- `/chat` 响应附带 citations
- `/chat_stream` 的 completed 事件附带 citations
- retrieval 失败时的降级路径
- 保持 completed 才触发 context memory 标准更新

当前不要求落地：

- 独立 RAG 微服务
- 长期记忆
- Agentic RAG
- 多模态 retrieval
- Case Workspace / 审批流
- 跨模块工作流系统

---

## 8. 修改规则

1. 不允许在 service 层直接调用 Redis client
2. 不允许手写 key / TTL / scope 逻辑
3. 不允许让 `request_assembler` 之外的模块决定上下文与知识块顺序
4. 不允许在 service 层直接实现 parser / chunker / embedding / index 细节
5. 不允许把 citations 做成模型自由生成字符串，必须基于 retrieval 结果装配
6. retrieval 相关改动必须同时考虑同步链路与流式 completed 收口

---

## 9. Code Review 清单

1. services 是否仍保持“编排层”定位？
2. 是否把底层实现正确下沉到了 context / rag / providers？
3. request_assembler 是否仍是唯一装配中枢？
4. 装配顺序是否为：
   - system
   - working memory
   - rolling summary
   - retrieved knowledge
   - recent raw
   - user
5. completed / failed / cancelled 收口是否仍符合 Phase 4 / Phase 5 约束？
6. `/chat` 与 `/chat_stream` 是否都正确处理了 citations？
7. retrieval 失败时是否具备可控降级？
8. 是否没有把向量库或 embedding 厂商细节直接暴露到 service 业务逻辑中？

---

## 10. 测试要求

至少覆盖：

1. 同步聊天链路在启用 retrieval 后仍可正常工作
2. 流式聊天 completed 事件可返回 citations
3. delta 阶段不发送 citations
4. retrieval 失败时可降级
5. completed assistant message 才进入标准 memory update
6. failed / cancelled assistant message 不污染后续 request assembly
7. request_assembler 中 knowledge block 注入顺序正确

---

## 11. 一句话总结

`app/services/` 在 Phase 6 中的职责，是在不破坏 Phase 4 / Phase 5 已有同步与流式会话主链路的前提下，把 retrieval、knowledge block 与 citations 以编排方式接入现有 chat core，而不是承担底层 RAG 实现本身。