# app/services/AGENTS.md

> 更新日期：2026-04-09

## 1. 文档定位

本文件定义 `app/services/` 的职责、边界、结构约束与 review 标准。  
当前阶段，本文件临时同时承担该模块的 AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW 职责。

---

## 2. 模块定位

`app/services/` 是系统的应用编排层。  
它负责把 API 层与 context / prompts / providers 串成完整业务链路。

当前阶段建议围绕以下职责组织：

- `chat_service.py`：同步聊天主链路
- `request_assembler.py`：统一请求装配入口
- `streaming_chat_service.py`：流式聊天编排入口（本轮允许新增）
- `cancellation_registry.py`：运行时取消协调（本轮允许新增）

---

## 3. 本层职责

1. 承接同步与流式两类会话用例
2. 协调 context / prompts / providers
3. 管理 assistant message 生命周期
4. 管理 started / delta / completed / error / cancelled 收口
5. 在 completed 时触发 Phase 4 的 layered memory 标准更新
6. 管理 cancel / timeout / failure 的业务编排

---

## 4. 本层不负责什么

1. 不负责 HTTP 路由
2. 不负责 provider SDK / HTTP 适配细节
3. 不负责 context store 的底层存储实现
4. 不负责定义共享数据契约本身
5. 不负责 SSE 文本协议
6. 不负责把 summary / reducer 算法写死在 service 里

---

## 5. 依赖边界

### 允许依赖
- `app/context/`
- `app/prompts/`
- `app/providers/`
- `app/schemas/`
- `app/observability/`

### 禁止依赖
- `app/api/`
- Redis client、key 拼接、TTL 细节

---

## 6. 架构原则

### 6.1 编排优先，细节下沉
services 负责“编排”，不负责“底层实现”。

### 6.2 request_assembler 是上下文装配中枢
assembler 是唯一允许决定以下顺序的地方：

1. system prompt
2. working memory block
3. rolling summary block
4. recent raw messages
5. current user input

### 6.3 生命周期调度必须收敛在 services
API 不负责状态机；context 不负责流式业务编排；providers 不负责外部会话生命周期。

### 6.4 completed 收口必须与 Phase 4 对齐
- completed：执行标准 `update_after_chat_turn`
- failed / cancelled：只更新消息状态，不走标准 memory update
- delta：只负责传输与聚合，不写 rolling summary / working memory

---

## 7. 当前阶段能力声明

当前本轮必须落地：

- `/chat/stream` 对应的 service 主链路
- cancel / timeout / failure 编排
- assistant placeholder + lifecycle 管理
- canonical stream event 生成
- completed 才触发 context memory 标准更新

当前不要求落地：

- WebSocket
- 多模态
- Tool / RAG / 长期记忆
- 跨模块工作流系统

---

## 8. 修改规则

1. 不允许在 service 层直接调用 Redis client
2. 不允许手写 key / TTL / scope 逻辑
3. 不允许让 `request_assembler.py` 直接依赖 store 私有实现
4. 不允许在每个 delta 上执行标准 memory update
5. 不允许 services 直接输出 SSE 文本协议
6. 改动主链路时必须同步更新测试与文档

---

## 9. Code Review 清单

1. services 是否仍然是编排层？
2. 是否绕过 `ContextManager` 直接操作 store？
3. started / delta / completed / error / cancelled 顺序是否清晰？
4. request assembly 顺序是否仍固定？
5. non-completed assistant message 是否被排除在后续上下文装配之外？
6. cancel / timeout / failure 是否保持稳定外部语义？

---

## 10. 测试要求

至少覆盖：

1. 同步 `chat_from_user_prompt` 成功路径
2. `request_assembler` 固定顺序装配
3. 流式 success / error / cancel 路径
4. completed 后 layered memory 更新
5. failed / cancelled 不进入标准 memory update
6. `reset_context` session / conversation 路径

---

## 11. 一句话总结

`app/services/` 在 Phase 5 中的职责不是实现 SSE 协议，也不是实现 provider SDK 细节，而是把同步与流式两条会话主链路稳定编排进现有系统，并确保只有 completed 才进入 Phase 4 的记忆闭环。
