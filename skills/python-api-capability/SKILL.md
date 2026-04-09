---
name: python-api-capability
description: 用于为 vi_ai_core_service 搭建和标准化面向 C 端 AI 应用的 Python API 接入层骨架。重点关注薄路由、service 委托、会话标识、流式输出预留、多模态输入、稳定响应契约与 API 边界。
last_updated: 2026-04-09
---

# 目的

本 skill 用于指导 `vi_ai_core_service` 中 API 接入层的新增、整理与标准化工作。

它面向的是当前主流 C 端 AI 应用产品常见的 API 接入模式，而不只是传统的“同步文本接口”：

- 多轮 chat API
- health / readiness 端点
- streaming response endpoint 预留
- 会话/对话标识透传
- 多模态输入入口预留
- 工具调用、安全校验、观测埋点等后续能力预留

本 skill 的核心目标是确保 API 层始终保持正确职责：

- 负责协议接入
- 负责请求解析与校验
- 负责 session / conversation 级输入承接
- 负责向 service 层委托
- 负责输出稳定、清晰、可扩展的响应
- 不承担底层业务编排与 provider 适配细节

本 skill 是 **任务执行规范**，不是模块治理文档。  
使用本 skill 前，应先阅读：

1. 项目根目录 `AGENTS.md`
2. 项目根目录 `PROJECT_PLAN.md`
3. 项目根目录 `ARCHITECTURE.md`
4. 项目根目录 `CODE_REVIEW.md`
5. `app/api/AGENTS.md`

---

# 当前阶段约束（必须遵守）

在 `vi_ai_core_service` 当前阶段，执行本 skill 时必须默认遵守以下范围：

- `/chat` 仍是非流式主路径。
- API 层当前只需要稳定承接 `session_id` / `conversation_id` 并委托给 service。
- `streaming`、多模态、tools、结构化输出 仅允许预留字段或预留接口，不做真实功能落地。
- API 层必须保持薄路由，只依赖 service-facing contract 与 service-facing errors。
- 不为 Phase 4 的 layered memory 引入新的 admin/debug memory API。
- 不为未来能力引入超出当前阶段的大型抽象或平台化改造。

---

# 适用场景

在以下场景中使用本 skill：

- 新增 `app/api/` 下的 chat / health / status / conversation 类接口
- 新增支持多轮对话的 HTTP API
- 为 streaming / SSE / chunked response 预留接口骨架
- 为附件输入、图片输入、文件输入预留 API 入口
- 为后续工具调用、moderation、observability 增加 API 接入钩子
- 规范化 API 层与 service 层之间的边界
- 整理现有 API 层结构，使其更贴近 C 端 AI 应用产品后端风格

---

# 不适用场景

以下场景不应使用本 skill：

- 在 API 模块中直接接入 vendor SDK
- 在 API 模块中实现 provider-specific 参数映射
- 在 API 模块中实现 RAG / Agent / workflow 主逻辑
- 在 API 模块中实现数据库、队列、分布式状态核心逻辑
- 在 API 模块中直接实现复杂 context policy
- 在 API 模块中直接拼 prompt 模板
- 在 API 模块中直接实现 layered memory store 细节

---

# 分层职责

API 层负责：

- HTTP/协议接入
- 请求解析与校验
- `conversation_id` / `session_id` / `request_id` 等标识承接
- 用户输入与附件输入入口承接
- 同步 / 流式响应模式选择
- 调用 `app/services/` 完成业务编排
- 返回稳定的响应结构与错误语义
- 为 observability / moderation / abuse guardrails 预留接入点

API 层不负责：

- provider SDK 调用
- prompt 模板读取与渲染
- context store 底层读写
- working memory / rolling summary / reducer 实现
- 业务主流程编排
- 厂商特定协议适配
- 返回原始厂商对象

---

# 必要输入

使用本 skill 前，应明确以下输入信息：

1. 本次接口属于哪个产品场景：
   - chat
   - health
   - conversation
   - session
   - admin/debug（若当前阶段允许）
2. 是否是同步接口、流式接口，还是为实时能力预留接口
3. 是否需要承接：
   - conversation_id
   - session_id
   - message_id
   - request_id
4. 是否需要承接多模态或附件输入
5. 该接口应调用哪个 service
6. 输入请求模型与输出响应模型是否已明确
7. 当前阶段是否真的需要新增该接口

---

# 预期输出

使用本 skill 后，交付物应至少包括：

1. 位于 `app/api/` 下的 API 路由模块
2. 薄且清晰的 route handler
3. 明确的 service 委托关系
4. 显式、稳定的请求/响应结构
5. conversation / session 标识入口（如场景需要）
6. streaming 预留或支持路径（如场景需要）
7. 多模态/附件输入预留字段（如场景需要）
8. 最小可运行或可验证说明
9. 必要时补充测试

---

# 必要流程

1. 先确认本次需求是否真的属于 API 层。
2. 先检查根目录文档与 `app/api/AGENTS.md`。
3. 明确该接口属于同步、流式还是未来实时交互入口。
4. 明确是否需要 session / conversation 标识。
5. 在 `app/api/` 下创建或调整路由模块。
6. 保持 route handler 薄，仅负责：
   - 请求接收
   - 参数校验
   - 标识透传
   - 调用 service
   - 返回响应
7. 所有业务编排逻辑下沉至 `app/services/`。
8. 所有响应结构应尽量对齐系统 canonical schema。
9. 为错误映射、取消、幂等、观测预留最小扩展点。
10. 对照 checklist 自检。
11. 若改动影响接口契约、边界或测试行为，需同步更新文档与测试。

---

# 设计规则

## 1. 薄路由优先

API handler 只做接入，不做核心业务处理。

## 2. 面向 C 端对话产品的输入模型

API 层设计时，应优先考虑：
- 多轮 conversation
- session 标识
- 用户消息列表
- 附件/图片/文件输入
- 流式输出预留

而不是只按一次性纯文本请求设计。

## 3. 双态会话兼容

API 层应允许未来同时支持：
- 客户端自带历史的 stateless 模式
- 服务端保留 conversation/session 的 stateful 模式

## 4. 统一走 service 层

正常业务路径下，API 层必须通过 `app/services/` 进入系统主链路。

## 5. 输入输出显式

请求、响应、错误语义必须清晰，不能暴露厂商私有结构。

## 6. 不泄漏 layered memory 实现细节

Phase 4 中 API 层最多承接 `session_id` / `conversation_id`，不得把 store key、默认 scope、working memory schema 等内部实现细节泄漏到外部协议层。

## 7. 为流式和实时能力预留接口思维

即使当前先不完整实现，也不能把 API 结构写死成只支持同步短文本返回。

## 8. 当前阶段避免过度建设

当前不提前实现完整 auth / quota / billing / realtime infra，但要为这些能力预留清晰边界。

---

# 验证标准

一个合格的面向 C 端 AI 应用的 API skeleton，至少应满足：

- 文件落位正确
- handler 足够薄
- 业务逻辑委托给 service
- 支持 conversation/session 级输入建模或预留
- 无 vendor SDK 直接依赖
- 输出结构稳定
- 支持未来 streaming / attachment / tools 扩展
- 至少具备基本 smoke validation 能力

---

# 完成标准

本 skill 任务完成，至少表示：

1. API 路由代码已落在正确目录
2. API 层边界未被破坏
3. handler 未承载复杂编排逻辑
4. 调用链清晰指向 service 层
5. 对 C 端 AI 应用常见输入形态有合理预留
6. 输入输出可读、可测、可维护
7. 已通过 checklist 自检
8. 必要时已同步测试与文档

---

# 备注

本 skill 适用于当前 `vi_ai_core_service` 的 API 接入层建设阶段。  
未来如果 API 层复杂度提升，可继续细分为：

- python-api-streaming-skeleton
- python-api-session-conversation-skeleton
- python-api-webhook-skeleton
- python-api-observability-guardrails-skeleton

---

# 编码前输出要求

开始编码前，必须先输出：

1. 任务理解与范围边界（明确当前阶段 `/chat` 仍为非流式主路径）
2. 文件级改动计划（包含新增/修改/不改）
3. 风险与假设
4. 验证计划（至少包含路由、错误映射与标识透传验证）

---

# 编码后输出要求

完成编码后，必须输出：

1. 文件级变更清单与原因
2. 接口契约变化说明（若无变化也要明确说明）
3. 测试与验证结果
4. 文档回写说明
5. 未做项与后续 API 能力建议
