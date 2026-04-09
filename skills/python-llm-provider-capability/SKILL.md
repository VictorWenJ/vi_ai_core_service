---
name: python-llm-provider-capability
description: 用于为 vi_ai_core_service 搭建和标准化面向主流 C 端 AI 应用的 LLM Provider 层。当前聚焦 Phase 5：在保持非流式文本 chat 主路径稳定的前提下，落地文本 streaming 的 provider 统一抽象、chunk 归一化与收口字段。
last_updated: 2026-04-09
---

# 目的

本 skill 用于指导 Provider 层的新增、整理、标准化与升级工作。

当前目标是为 `app/providers/` 建立一个：

- 抽象清晰
- 能力可声明
- 可扩展
- 易于新增厂商
- 可统一归一化
- 面向非流式与流式文本输出

的 Provider 层实现规范。

---

# 当前阶段约束（必须遵守）

- provider 层必须稳定：
  - 非流式文本 chat 主路径
  - 文本 streaming 主路径
- `streaming` 是本轮真实落地能力，不再只是预留
- 多模态、tools/function calling、结构化输出 仍只做预留
- provider 输出的是 canonical response / canonical stream chunk，而不是 SSE

---

# 分层职责

Provider 层负责：

- 厂商 SDK / HTTP API 适配
- canonical request -> vendor request
- vendor response -> canonical response
- vendor stream chunk -> canonical stream chunk
- finish_reason / usage / provider error 提取
- provider capability 声明

Provider 层不负责：

- 业务主流程编排
- SSE 协议序列化
- assistant message 生命周期状态机
- context store 管理

---

# 设计规则

1. Streaming 是一等公民
2. provider 只输出 canonical stream，不输出 SSE
3. 优先复用同协议家族
4. 多模态、tools、structured output 仍然保留边界

---

# 验证标准

至少满足：

- non-streaming 不回归
- streaming 主路径可用
- chunk / finish / usage / error 可归一化
- 服务层不需要理解厂商私有事件结构
- provider 不输出 SSE 文本协议
