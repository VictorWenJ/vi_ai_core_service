# ARCHITECTURE.md

> 更新日期：2026-04-09

## 1. 文档定位

本文件定义 `vi_ai_core_service` 的总体架构、分层职责、依赖方向与调用关系。

---

## 2. 架构目标

- 建立边界清晰的 AI 服务分层结构
- 让不同能力在不同目录中各司其职
- 让系统具备前端可接入的流式会话交付能力
- 为后续 Tool、RAG、Agent 预留清晰边界

---

## 3. 当前总体分层

### API 接入层（`app/api/`）
职责：
- 暴露 HTTP 接口
- 解析请求
- 返回同步响应
- 输出 SSE 流式响应
- 暴露 cancel/reset 等控制入口

### 应用编排层（`app/services/`）
职责：
- 承接同步与流式两类会话用例
- 协调 context / prompts / providers
- 管理 assistant message 生命周期
- 管理 cancel / timeout / failure 收口

### 上下文管理层（`app/context/`）
职责：
- 管理 conversation-scoped 短期状态
- 管理 recent raw / rolling summary / working memory
- 管理 message lifecycle 相关状态字段
- 规定 completed 才进入标准 memory update

### Prompt 资产层（`app/prompts/`）
职责：
- 管理 Prompt 模板
- 提供渲染能力

### 模型 API 接入层（`app/providers/`）
职责：
- 对接不同厂商
- 归一化非流式结果
- 归一化流式 chunk / finish / usage / error

### 可观测性基础设施层（`app/observability/`）
职责：
- 统一结构化日志
- 记录 request_id / assistant_message_id / status / stream_event_count 等定位字段

### 数据模型层（`app/schemas/`）
职责：
- 定义请求、响应、stream event、cancel contract、message lifecycle 相关契约

---

## 4. 工程基础设施平面

`infra/` 负责：

- Dockerfile
- compose 编排
- app + redis 本地联调
- 运行时环境变量样例

`infra/` 不进入业务依赖链。

---

## 5. 总体依赖方向

业务依赖方向：

`api -> services -> context/prompts/providers -> schemas`

其中：

- `observability` 为横切基础设施层，可被 `api/services/providers` 依赖
- `providers` 不能依赖 `api/services/context`
- `context` 不能依赖 `api/services/providers`

---

## 6. 当前调用关系

### 6.1 同步聊天链路

1. 请求进入 `/chat`
2. API 校验并委托给 service
3. service 调用 `request_assembler`
4. assembler 按固定顺序装配：
   - system prompt
   - working memory block
   - rolling summary block
   - recent raw messages
   - current user input
5. service 调用 provider 非流式请求
6. provider 返回归一化结果
7. service 执行 completed 态 context update
8. API 输出响应

### 6.2 流式聊天链路

1. 请求进入 `/chat/stream`
2. API 建立 SSE 响应
3. service 生成 `request_id` 与 `assistant_message_id`
4. service 写入 user message 与 assistant placeholder
5. API 先输出 `response.started`
6. service 调用 provider 流式请求
7. provider 输出 canonical stream chunk
8. service 推进 lifecycle 并生成 canonical stream event
9. API 将 event 序列化为 SSE
10. 正常完成时：
   - service 写回 completed assistant message
   - service 执行 Phase 4 标准 context update
   - API 输出 `response.completed`
11. 异常或取消时：
   - service 写回 `failed` / `cancelled`
   - 不进入标准 memory update
   - API 输出 `response.error` 或 `response.cancelled`

---

## 7. Phase 4 与 Phase 5 的衔接原则

- Phase 4 的 policy pipeline 不变：
  `selection -> truncation -> deterministic summary -> serialization`
- Phase 5 不改变 request assembly 顺序
- 只有 completed assistant message 才进入标准 memory update
- non-completed assistant message 默认不参与后续 request assembly

---

## 8. SSE 协议架构约束

默认事件类型建议收敛为：

- `response.started`
- `response.delta`
- `response.completed`
- `response.error`
- `response.cancelled`
- `response.heartbeat`

约束：

- API 层负责 SSE 文本协议
- services 层负责事件顺序与生命周期
- providers 层只输出 canonical stream chunk，不输出 SSE
- observability 只记录事件，不驱动事件
