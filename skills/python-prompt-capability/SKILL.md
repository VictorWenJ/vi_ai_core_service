---
name: python-prompt-capability
description: 用于为 vi_ai_core_service 搭建和标准化面向主流 C 端 AI 应用的 Prompt 资产层。重点关注模板资产管理、分层指令组合、registry/renderer、系统提示与场景提示分离、多模态输入预留、工具调用与结构化输出提示约束，以及与 service/provider/context 的清晰边界。
last_updated: 2026-04-06
---

# 目的

本 skill 用于指导 `vi_ai_core_service` 中 Prompt 资产层的新增、整理、标准化与升级工作。

它面向的是当前主流 C 端 AI 应用产品常见的 Prompt 后端形态，而不只是早期“一个 system prompt 文件 + 一个 renderer”的简单模式。

本 skill 的目标是为 `app/prompts/` 建立一个：

- 结构清晰
- 资产可发现
- 组合方式明确
- 可版本化
- 可扩展
- 便于测试
- 不绑定单一 provider

的 Prompt 层实现规范。

本 skill 重点解决的问题包括：

- 如何管理系统提示、场景提示、模板提示等不同类型的 Prompt 资产
- 如何建立 registry 与 renderer
- 如何支持分层指令组合
- 如何为工具调用、结构化输出、多模态输入等场景预留 Prompt 扩展点
- 如何避免把 Prompt 文本散落到 service / provider / API 层
- 如何为未来 Prompt 版本治理、A/B 试验、缓存友好结构预留空间

本 skill 是 **任务执行规范**，不是模块治理文档。  
使用本 skill 前，应先阅读：

1. 项目根目录 `AGENTS.md`
2. 项目根目录 `PROJECT_PLAN.md`
3. 项目根目录 `ARCHITECTURE.md`
4. 项目根目录 `CODE_REVIEW.md`
5. `app/prompts/AGENTS.md`

---

# 当前阶段约束（必须遵守）

在 `vi_ai_core_service` 当前阶段，执行本 skill 时必须默认遵守以下范围：

- Prompt 层只要求“基础资产目录 + registry + renderer + 默认 chat system prompt”稳定可用。
- tools、结构化输出、多模态等仅做提示层预留，不做完整 orchestration engine。
- 不把 Prompt 层扩展成策略平台或业务规则引擎。
- 重点是收敛散落 Prompt、稳定渲染行为、保持与 service/provider/context 的边界清晰。

---

# 适用场景

在以下场景中使用本 skill：

- 新增 `app/prompts/` 下的 Prompt 模板目录
- 新增 system prompt / 场景提示词（scenario prompt） / fallback prompt
- 新增或整理 registry / renderer
- 把散落在 service / script 中的 prompt 文本收敛到 Prompt 层
- 为多轮对话、工具调用、结构化输出场景补充 Prompt 资产
- 为 future variants / versioning / A/B test 做结构准备
- 校正 Prompt 层边界，使其更符合主流 C 端 AI 应用后端结构

---

# 不适用场景

以下场景不应使用本 skill：

- provider SDK 接入
- API 路由设计
- context store 管理
- 业务主流程编排
- 工具执行循环
- Agent 规划
- 检索 / RAG 管线
- 复杂 prompt orchestration engine 的一次性实现
- 在 Prompt 层中写业务规则引擎

---

# 分层职责

Prompt 层负责：

- 管理 Prompt 模板资产
- 定义 Prompt 目录组织方式
- 提供 registry 用于查找模板
- 提供 renderer 用于模板渲染与组合
- 区分不同 Prompt 类型，例如：
  - 基础系统提示词（base system prompt）
  - 产品策略提示词（product policy prompt）
  - 场景提示词（scenario prompt）
  - 输出约束提示词（输出约束（output constraint） prompt）
  - 工具使用引导提示词（工具使用引导（tool-use guidance） prompt）
- 为多模态输入、结构化输出、工具调用等场景预留提示层扩展位
- 为未来版本治理、缓存友好结构、变体选择预留空间

Prompt 层不负责：

- provider SDK / HTTP 调用
- 业务主流程编排
- conversation/session 存储
- tool 执行
- fallback / routing 策略
- 用户态业务规则引擎
- moderation / abuse 决策本身

---

# 必要输入

使用本 skill 前，应明确以下输入信息：

1. 当前要新增或改造的是哪类 Prompt 资产：
   - system
   - scenario
   - 输出约束（output constraint）
   - tool guidance
   - multimodal prompt support
2. 该 Prompt 对应哪个产品场景：
   - chat
   - assistant reply
   - summarize
   - rewrite
   - task guidance
   - 结构化输出
3. Prompt 是否需要变量渲染
4. Prompt 是否需要分层组合
5. 是否需要为 tools / function calling 预留提示结构
6. 是否需要为 结构化输出 / JSON mode（JSON 模式） 预留约束提示
7. 当前是否只做最小落地，还是同时补 registry / renderer / variants 能力

---

# 预期输出

使用本 skill 后，交付物应至少包括：

1. 位于 `app/prompts/templates/` 下的 Prompt 模板文件
2. 清晰的模板目录结构
3. registry 中显式的模板标识与查找逻辑
4. renderer 中稳定、可测试的渲染逻辑
5. system / scenario / constraint 等 Prompt 分层思路或落地
6. 对 tools / 结构化输出 / multimodal 的扩展位
7. 最小运行与验证说明
8. 必要时补充测试

---

# 必要流程

1. 先确认本次需求是否真的属于 Prompt 层。
2. 先检查根目录文档与 `app/prompts/AGENTS.md`。
3. 明确 Prompt 属于哪一类资产。
4. 按场景将模板放入 `app/prompts/templates/` 的合理目录中。
5. 在 registry 中显式注册模板标识，不要靠隐式路径猜测。
6. 在 renderer 中实现基础变量渲染与必要的分层组合。
7. 若存在 system / scenario / 输出约束（output constraint） / tool guidance，应明确分层边界。
8. 保持 Prompt 层 provider-agnostic，不嵌入厂商私有请求协议。
9. 为未来 variants / versioning / cache-friendly blocks 预留结构，但当前不做过度复杂化。
10. 对照 checklist 自检。
11. 若改动影响 Prompt 资产结构、契约或测试行为，需同步更新文档与测试。

---

# 设计规则

## 1. Prompt 是资产，不是内联文本

Prompt 应被视为长期维护的工程资产，而不是散落在 service、script、provider 中的字符串常量。

## 2. 分层指令组合

Prompt 层设计时，应优先考虑分层组合，而不是把所有要求塞进一个超长 system prompt。

典型层次可包括：

- 基础系统指令（base system instruction）
- 产品/安全指令（product / safety instruction）
- 场景特定指令（scenario-specific instruction）
- 输出约束（output constraint）
- 工具使用引导（tool-use guidance）
- 运行时变量注入（runtime variable injection）

当前可以不全部实现，但结构上应允许未来演进。

## 3. 默认保持 Provider 无关

Prompt 层不应绑定某个 provider 的私有字段名、SDK 参数名或响应对象格式。

Prompt 应服务于系统内部语义，不应服务于厂商私有协议。

## 4. Prompt 层应支持真实产品形态

Prompt 结构设计时，应面向主流 C 端 AI 产品常见形态：

- 多轮对话
- 工具调用提示
- 结构化输出约束
- 多模态输入说明
- 长上下文场景下的稳定 system blocks
- 可缓存的稳定提示块

## 5. 保持稳定区块可发现

对于稳定且可能重复使用的 Prompt 片段，应允许未来做：

- 独立模板化
- 版本治理
- 缓存友好组织
- 变体选择

不要把所有提示写成一个不可拆的大文件。

## 6. 渲染器必须确定性

Renderer 行为必须尽量确定、易读、易测。

不要让 renderer 变成隐式业务路由器或复杂决策引擎。

## 7. Prompt 资产与业务路由分离

Prompt 层负责“提示内容怎么存、怎么找、怎么渲染”，  
不负责“什么时候走哪个产品流程”。

## 8. 当前阶段避免过度建设

当前阶段不应在 Prompt 层提前引入：

- 复杂 prompt routing engine
- 复杂策略 DSL
- 大型实验平台
- 与 provider 强绑定的高级控制逻辑

先把资产层、registry、renderer、分层组合思路打稳。

---

# 验证标准

一个合格的面向主流 C 端 AI 应用的 Prompt 层实现，至少应满足：

- 模板位于正确目录
- 模板命名与组织清晰
- registry 查找逻辑显式
- renderer 渲染逻辑稳定
- Prompt 资产不再大量散落在其他层
- system / scenario / constraint 等层次有清晰思路或落地
- 对 tools / 结构化输出 / multimodal 具备扩展意识
- 保持 provider-agnostic
- 当前阶段未引入不必要的复杂引擎

---

# 完成标准

本 skill 任务完成，至少表示：

1. Prompt 模板已落在正确目录
2. Prompt 资产结构清晰
3. registry 与 renderer 最小可用
4. Prompt 层边界未被破坏
5. service / provider / API 中无不必要的硬编码 Prompt 文本
6. 对主流 C 端 AI 产品常见提示层需求有合理预留
7. 已通过 checklist 自检
8. 必要时已同步测试与文档

---

# 备注

本 skill 适用于当前 `vi_ai_core_service` 的 Prompt 资产层建设阶段。  
未来若 Prompt 层复杂度提升，可继续细分为：

- python-prompt-variants-skill
- python-prompt-structured-output-skill
- python-prompt-tool-guidance-skill
- python-prompt-cache-friendly-layout-skill
- python-prompt-governance-and-versioning-skill

---

# 编码前输出要求

开始编码前，必须先输出：

1. 任务理解与范围边界（仅基础资产层，不做 orchestration engine）
2. 模板/registry/renderer 的文件级改动计划
3. 风险与假设
4. 验证计划（模板查找与渲染稳定性）

---

# 编码后输出要求

完成编码后，必须输出：

1. 文件级变更清单与原因
2. Prompt 资产变化说明
3. 测试与验证结果
4. 文档回写说明

---

# 资产与验证索引

1. 检查清单：`assets/prompt_capability_checklist.md`
2. 测试矩阵：`assets/prompt_test_matrix.md`
3. 参考文档：`references/prompt_boundaries_and_acceptance.md`

---

# 治理联动

执行本 skill 时必须遵循统一闭环：

`根目录文档 -> app/prompts/AGENTS.md -> 本 skill -> 代码实现 -> review -> 文档回写`

强制要求：

1. 未完成根目录四文档与模块 AGENTS 阅读，不进入代码实现。
2. 改动后必须按根 `CODE_REVIEW.md`、模块 `AGENTS.md`、本 skill checklist 联合自审。
3. 若 Prompt 资产结构、渲染行为或测试事实变化，必须同步更新对应文档与测试。

