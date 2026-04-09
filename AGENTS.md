# AGENTS.md

> 更新日期：2026-04-09

## 1. 文档定位

本文件是 `vi_ai_core_service` 的仓库级协作与治理总纲。  
执行任何实现任务时，必须先读：

1. 根目录 `AGENTS.md`
2. 根目录 `PROJECT_PLAN.md`
3. 根目录 `ARCHITECTURE.md`
4. 根目录 `CODE_REVIEW.md`
5. 目标模块 `AGENTS.md`
6. 对应 skill 文档

---

## 2. 项目定位

`vi_ai_core_service` 是 VI AI Project 的 Python AI 核心服务。  
当前目标不是做“大而全”的平台，而是先把面向主流 C 端 AI 应用的核心会话后端打稳。

当前阶段聚焦：

- 多模型接入
- Prompt 资产组织
- conversation-scoped 短期记忆
- 流式与非流式聊天交付
- 对外 API
- 最小可观测性
- 稳定数据契约
- 本地运行与交付（`infra/`）

---

## 3. 当前项目范围

当前仍限定为七层业务/系统分层：

1. API 接入层（`app/api/`）
2. 应用编排层（`app/services/`）
3. 上下文管理层（`app/context/`）
4. Prompt 资产层（`app/prompts/`）
5. 模型 API 接入层（`app/providers/`）
6. 可观测性基础设施层（`app/observability/`）
7. 数据模型层（`app/schemas/`）

`infra/` 是项目级工程基础设施治理域，不属于第八层业务层。

---

## 4. 当前轮次主任务（强约束）

当前轮次为：

**Phase 5：Streaming Chat & Conversation Lifecycle**

### 本轮必须完成

- 保持同步 `/chat` 主链路可用
- 新增 `/chat_stream`（SSE）
- 新增 `/chat_stream_cancel`
- assistant message 生命周期：
  - `created`
  - `streaming`
  - `completed`
  - `failed`
  - `cancelled`
- 引入 `request_id`、`assistant_message_id`、`finish_reason`、`usage`、`latency`、`error_code`
- 保持 Phase 4 的 layered short-term memory 不被破坏
- 只有 `completed` 的 assistant message 才进入标准 context memory 更新闭环

### 本轮明确不做

- WebSocket 主协议
- Tool calling
- RAG / 长期记忆
- Agent runtime
- 多模态 streaming
- tracing / metrics / APM 平台化

---

## 5. 全局依赖方向

整体业务依赖方向仍应遵守：

`api -> services -> context/prompts/providers -> schemas`

其中：

- `api` 负责 HTTP / SSE 协议输出
- `services` 负责同步与流式会话编排
- `context` 负责会话状态与记忆收口规则
- `providers` 负责厂商适配与流式 chunk 归一化
- `schemas` 负责共享契约
- `observability` 负责结构化日志

---

## 6. 全局开发原则

- 显式优于隐式
- 稳定优于花哨
- 分层优于混写
- 可测试优于难验证
- 可审查优于“能跑就行”

### Phase 5 额外原则

- 同步与流式两条链路必须并存
- 不允许在每个 delta 上执行标准 memory update
- 不允许 provider 直接输出 SSE 文本
- 不允许把 cancel 语义简化为“客户端断开连接就算取消成功”
