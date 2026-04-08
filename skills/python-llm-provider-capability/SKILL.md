---
name: python-llm-provider-capability
description: 用于为 vi_ai_core_service 搭建和标准化面向主流 C 端 AI 应用的 LLM Provider 层。重点关注统一 provider 抽象、厂商协议适配、流式/非流式输出、多模态输入、工具调用、结构化输出、能力声明、响应归一化以及与 service 层的清晰解耦。
last_updated: 2026-04-06
---

# 目的

本 skill 用于指导 `vi_ai_core_service` 中模型 Provider 层的新增、整理、标准化与升级工作。

它面向的是当前主流 C 端 AI 应用产品常见的模型接入方式，而不是早期单一“文本 chat completion 调用”模式。

本 skill 的目标是为 `app/providers/` 建立一个：

- 抽象清晰
- 能力可声明
- 可扩展
- 易于新增厂商
- 可统一归一化
- 面向流式、多模态、工具调用与结构化输出

的 Provider 层实现规范。

本 skill 重点解决的问题包括：

- 如何定义统一的 LLM provider 抽象
- 如何适配不同厂商 API 协议
- 如何在 provider 层吸收厂商差异
- 如何对流式与非流式结果做统一归一化
- 如何承接多模态输入、工具调用、结构化输出等常见能力
- 如何声明 provider capability
- 如何保证 service 层不直接依赖厂商 SDK
- 如何避免把 provider 层写成业务编排层

本 skill 是 **任务执行规范**，不是模块治理文档。  
使用本 skill 前，应先阅读：

1. 项目根目录 `AGENTS.md`
2. 项目根目录 `PROJECT_PLAN.md`
3. 项目根目录 `ARCHITECTURE.md`
4. 项目根目录 `CODE_REVIEW.md`
5. `app/providers/AGENTS.md`

---

# 当前阶段约束（必须遵守）

在 `vi_ai_core_service` 当前阶段，执行本 skill 时必须默认遵守以下范围：

- provider 层当前只要求稳定非流式文本 chat 主路径。
- `streaming`、多模态、tools/function calling、结构化输出 仅做 contract/capability 预留，不做真实功能落地。
- 不引入复杂 routing/fallback/retry 引擎，不做大型 provider 平台化重构。
- 重点是保证 provider 抽象稳定、错误语义清晰、与 service 层边界清晰。

---

# 适用场景

在以下场景中使用本 skill：

- 新增一个 LLM provider
- 将业务代码中的厂商直调重构到 `app/providers/`
- 新增或整理 provider base abstraction
- 为 OpenAI 兼容 厂商做统一适配
- 新增 Anthropic / Gemini / OpenAI / DeepSeek / Doubao / Tongyi 等 provider 接入
- 新增流式输出支持
- 新增多模态输入支持（如 text + image/file metadata）
- 新增工具调用参数透传与结果归一化支持
- 新增结构化输出 / JSON mode（JSON 模式） 支持
- 补齐 provider capability 声明与测试矩阵
- 校正 provider 层与 service 层之间的边界

---

# 不适用场景

以下场景不应使用本 skill：

- 图像生成 provider
- 视频生成 provider
- 音频生成 / TTS / ASR provider
- embedding Provider（向量嵌入）
- reranker Provider（重排）
- RAG 管线
- Agent 工作流
- 工具执行编排
- prompt 资产管理
- context store 管理
- 数据库、队列或业务流程编排

---

# 分层职责

Provider 层负责：

- 厂商 SDK / HTTP API 适配
- 将系统内部 canonical request 映射为厂商请求
- 将厂商响应归一化为系统内部 canonical response
- 将流式 chunk 归一化为统一事件或统一增量结构
- 处理 provider 级配置校验
- 处理 provider 级能力声明
- 处理 provider 级错误分类与包装
- 向上层屏蔽厂商协议差异

Provider 层不负责：

- 业务主流程编排
- conversation/session 记忆管理
- prompt 模板组织与渲染
- tool 执行循环
- model routing / fallback 决策
- 跨 provider 业务策略
- 用户态功能逻辑

---

# 必要输入

使用本 skill 前，应明确以下输入信息：

1. 当前要接入或改造的是哪类 provider：
   - OpenAI Responses / Chat 风格
   - OpenAI 兼容 风格
   - Anthropic Messages 风格
   - Gemini generateContent / streamGenerateContent 风格
   - 其他独立协议风格
2. 该 provider 支持哪些能力：
   - 非流式
   - streaming
   - 多模态输入
   - tools / function calling
   - 结构化输出 / JSON mode（JSON 模式）
   - 用量提取
   - finish_reason / stop_reason
3. 当前系统内部的 canonical request / response 需要包含哪些字段
4. provider 需要读取哪些配置
5. provider 是否应复用已有 base class
6. 当前是否只做最小接入，还是同时补齐 capability 与 test matrix

---

# 预期输出

使用本 skill 后，交付物应至少包括：

1. 一个清晰的 provider 实现文件或 provider family 实现文件
2. 明确的 provider base / compatibility base 复用关系
3. provider capability 声明
4. canonical request -> vendor request 的映射实现
5. vendor response -> canonical response 的归一化实现
6. 若支持 streaming，则包含统一 chunk/event 归一化实现
7. provider 注册逻辑
8. 配置校验逻辑
9. 测试矩阵更新
10. 最小运行和验证说明

---

# 必要流程

1. 先确认本次需求是否真的属于 provider 层。
2. 先检查根目录文档与 `app/providers/AGENTS.md`。
3. 理解当前 provider 目录结构与已有 base abstraction。
4. 确认目标 provider 的协议族：
   - OpenAI 兼容
   - OpenAI 原生风格
   - Anthropic Messages 风格
   - Gemini 内容生成风格
   - 其他自定义风格
5. 明确该 provider 的 capability matrix。
6. 设计 canonical request / response / stream chunk 的映射方式。
7. 优先复用已有 base，不要重复实现共性逻辑。
8. 将厂商差异限制在 provider 层内部。
9. 在 registry 中完成 provider 注册。
10. 对照测试矩阵补充最小必要测试。
11. 若改动影响 provider contract、service 调用方式或测试行为，需同步更新文档与测试。

---

# 设计规则

## 1. 先统一规范契约（Canonical Contract First）

Provider 层必须优先围绕系统内部统一 contract 设计，而不是围绕某一家 SDK 设计。

canonical request 应至少允许未来承载：

- provider
- model
- messages / input items
- system instruction
- stream flag
- temperature / top_p / max_tokens
- tools
- tool_choice
- response_format / 结构化输出
- metadata
- optional 多模态输入 references

canonical response 应至少允许未来承载：

- content / output text
- output blocks / normalized content items（如后续需要）
- provider
- model
- usage
- finish_reason / stop_reason
- tool calls / 结构化输出 result（如适用）
- metadata
- raw response（仅在确有需要时）

---

## 2. 能力声明必须显式（Capability Declaration Is Explicit）

每个 provider 应显式声明自己支持什么，不要让上层靠猜测判断。

例如可声明：

- supports_streaming（支持流式）
- supports_multimodal_input（支持多模态输入）
- supports_tools（支持工具）
- supports_structured_output（支持结构化输出）
- supports_system_instruction（支持系统指令）
- supports_usage（支持用量统计）
- supports_response_format（支持响应格式）

---

## 3. 优先复用同协议家族（Prefer Family Reuse）

若某厂商协议与现有协议族兼容，应优先复用 family base。

例如：

- OpenAI 兼容 provider 应优先复用兼容基类
- 但不能为了复用而强行假装兼容
- 若协议差异已明显超过共享抽象承受范围，应单独实现

---

## 4. 流式能力是一等公民（Streaming Is First-Class）

当前主流 C 端 AI 产品后端，streaming 不是附加功能，而是核心能力之一。

Provider 层设计时应明确：

- 流式与非流式的统一 contract 关系
- chunk 的内容增量表示
- finish / stop 事件语义
- usage 是否在末尾或单独事件中提供
- 错误中断如何上抛

即使当前只先做最小支持，也不能把 provider 抽象写死成只支持一次性返回。

---

## 5. 多模态输入是一等公民（Multimodal Input Is First-Class）

Provider 层不能把请求模型写死成“只有纯文本 prompt”。

至少要允许未来承载：

- text
- image reference / image url / image file reference
- file reference
- lightweight attachment metadata

当前项目如果暂时只实现文本，也应在 contract 和接口设计上预留扩展空间。

---

## 6. 工具与结构化输出应留在规范层（Canonical Layer）

Provider 层应支持：

- tools / function schemas 的透传或映射
- tool call result 的归一化
- 结构化输出 / JSON mode（JSON 模式） / response_format 的映射

但 provider 层不负责：

- 工具执行循环
- 工具业务语义
- agent planning

---

## 7. 厂商原始细节应留在 Provider 内部

厂商私有字段、私有响应对象、私有 stop reason 细节，应尽量留在 provider 层内部。

如确需暴露，也应进入：

- metadata
- raw_response（原始响应）
- vendor_specific fields（谨慎）

而不是污染上层主业务 contract。

---

## 8. 路由与回退不应放在 Provider 层

模型路由、降级、fallback、provider selection policy，属于 service/application 层策略，不属于 provider 自身职责。

Provider 负责“我如何调用这一家”，  
而不是“我是否应该被选中”。

---

## 9. 保持面向业务的 Service 解耦

业务层不应直接调用 SDK client。  
正常路径下，业务应调用 service 层方法，例如：

- respond()
- stream_response()
- generate_reply()

而不是让 provider 设计反过来绑死业务入口名为某个厂商风格的 `chat_completion()`。

---

## 10. 当前阶段避免过度建设

当前阶段不应在 provider 层提前引入：

- 复杂统一路由器
- 跨 provider 自动 fallback 引擎
- 大型 capability negotiation framework
- image/video/audio generation family 抽象

先把主流 C 端 AI 文本/多模态理解型 provider 层做好。

---

# 验证标准

一个合格的面向主流 C 端 AI 应用的 provider 实现，至少应满足：

- provider 落位正确
- base / family base 复用合理
- canonical request 映射清晰
- canonical response 归一化清晰
- 流式能力有清晰支持或预留
- 多模态输入有清晰支持或预留
- tools / 结构化输出 有清晰支持或预留
- 无业务流程编排逻辑混入
- service 层不直接感知厂商 SDK

---

# 完成标准

本 skill 任务完成，至少表示：

1. provider 代码已落在正确目录
2. provider 抽象未被破坏
3. 厂商差异已被限制在 provider 层内部
4. request / response / stream mapping 清晰
5. 当前阶段需要的 capability 已显式声明
6. registry 已正确接入
7. 测试矩阵已覆盖核心行为
8. 已通过 checklist / validation 自检
9. 必要时已同步测试与文档

---

# 备注

本 skill 适用于当前 `vi_ai_core_service` 的主模型 Provider 层建设阶段。  
未来若 provider 层复杂度提升，可继续细分为：

- python-openai-compatible-provider-skill
- python-anthropic-messages-provider-skill
- python-gemini-provider-skill
- python-llm-provider-streaming-skill
- python-llm-provider-structured-output-skill

---

# 编码前输出要求

开始编码前，必须先输出：

1. 任务理解与当前阶段边界
2. Provider 文件级改动计划
3. request/response 归一化策略说明
4. 风险与验证计划

---

# 编码后输出要求

完成编码后，必须输出：

1. 文件级变更清单与原因
2. 能力声明变化说明
3. 测试矩阵覆盖情况
4. 文档回写说明

---

# 资产与验证索引

1. 检查清单：`assets/llm_provider_capability_checklist.md`
2. 测试矩阵：`assets/llm_provider_test_matrix.md`
3. 参考文档：`references/llm_provider_boundaries_and_compatibility.md`

---

# 治理联动

执行本 skill 时必须遵循统一闭环：

`根目录文档 -> app/providers/AGENTS.md -> 本 skill -> 代码实现 -> review -> 文档回写`

强制要求：

1. 未完成根目录四文档与模块 AGENTS 阅读，不进入代码实现。
2. 改动后必须按根 `CODE_REVIEW.md`、模块 `AGENTS.md`、本 skill checklist/test matrix 联合自审。
3. 若 request/response/stream contract、能力声明或测试事实变化，必须同步更新对应文档与测试。

