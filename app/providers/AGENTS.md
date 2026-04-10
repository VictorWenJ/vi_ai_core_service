# app/providers/AGENTS.md

> 更新日期：2026-04-10

## 1. 文档定位

本文件定义 `app/providers/` 的职责、边界、结构约束、开发约束与 review 标准。
当前阶段，本文件临时同时承担该模块的 `AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW` 职责。
执行 providers 相关任务时，必须先读根目录 `AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md`，再读本文件，再根据 skill `skills/python-llm-provider-capability/` 执行。

本文件不负责：

- 仓库级协作规则
- 你和我之间的交互流程
- 根目录阶段路线图
- 根目录级总体架构说明
- 根目录级 Code Review 总标准

这些内容分别由：

- 根目录 `AGENTS.md`
- 根目录 `PROJECT_PLAN.md`
- 根目录 `ARCHITECTURE.md`
- 根目录 `CODE_REVIEW.md`
- `CHAT_HANDOFF.md`

承担。

---

## 2. 模块定位

`app/providers/` 是系统的模型与厂商接入层。
它负责对接不同模型厂商，向上层提供统一的 chat completion 与 stream completion 能力，不承担业务编排职责。

当前阶段建议围绕以下职责组织：

- `base.py`：Provider 抽象与共享异常
- `openai_compatible_base.py`：OpenAI 兼容调用基类
- `openai_provider.py` / `deepseek_provider.py`：已实现 Provider
- `gemini_provider.py` / `doubao_provider.py` / `tongyi_provider.py`：脚手架 Provider
- `registry.py`：集中式 Provider 注册与成熟度描述

---

## 3. 本模块职责

1. 对接不同厂商的 chat completion 能力
2. 对接不同厂商的流式 completion 能力
3. 输出统一的非流式结果结构
4. 输出统一的流式 chunk 结构
5. 管理 provider 级配置、错误映射与兼容层
6. 维护已实现 Provider 与脚手架 Provider 的统一注册入口

---

## 4. 本模块不负责什么

1. 不负责 HTTP 路由
2. 不负责同步或流式 chat 主链路编排
3. 不负责 context state 管理
4. 不负责 request assembly
5. 不负责 retrieval / chunking / index 实现
6. 不负责 citation 生成
7. 不负责业务流程与阶段决策

---

## 5. 依赖边界

### 允许依赖
- `app/schemas/`（如需要共享基础契约）
- `app/observability/`
- 标准库
- 第三方 provider SDK / HTTP client（按当前实现需要）

### 禁止依赖
- `app/api/`
- `app/services/`
- `app/context/`
- `app/rag/`
- 向量库 SDK

### 原则
`app/providers/` 是能力提供层，不是业务编排层，也不是知识检索层。

---

## 6. 架构原则

### 6.1 provider 只输出能力，不决定业务
providers 只负责“怎么调用厂商”，不负责“何时调用、怎么编排”。

### 6.2 当前代码的抽象边界
- `BaseLLMProvider` 当前定义 chat 与可选 stream 的稳定接口
- `OpenAICompatibleBaseProvider` 负责 OpenAI 兼容厂商的共性适配
- 当前代码尚未落地 embedding provider 抽象与实现

### 6.3 canonical contract 优先
无论不同厂商返回什么结构，provider 层都必须向上层暴露稳定的统一结构。

### 6.4 provider 不关心 citations
provider 只负责生成，不负责 retrieval、citation 或外部知识增强逻辑。

### 6.5 streaming 与 non-streaming 都必须可替换
同一 provider 能力应尽量保持：
- 非流式结果可归一化
- 流式结果可归一化
- 错误与 finish reason 可归一化

---

## 7. 当前阶段能力声明

当前本轮必须保持稳定：

- 非流式 chat completion
- 流式 chat completion
- stream chunk 归一化
- finish / usage / error 归一化
- `openai` / `deepseek` 已实现 Provider 行为
- `gemini` / `doubao` / `tongyi` 脚手架行为与错误语义

当前代码事实补充：

- `ProviderRegistry` 通过 `maturity=implemented|scaffolded` 描述 Provider 成熟度
- 当前仓库没有 embedding provider 抽象、实现或测试
- Phase 6 中若要引入 embedding，必须先在代码中真实落地，再同步更新文档

当前本轮不要求：

- embedding 主链路
- 多模态 embedding 主链路
- 图像 / 音频 / 视频 embedding 主链路
- provider 层直接参与 retrieval
- provider 层直接感知 citations

---

## 8. 文档维护规则（强约束）

本文件属于 `app/providers/` 模块的治理模板资产。
后续任何更新，必须严格遵守以下规则：

### 8.1 基线规则
- 必须以当前文件内容为基线进行增量更新
- 不涉及变动的内容不得改写
- 未经明确确认，不得重写文件整体风格

### 8.2 冻结规则
未经明确确认，不得擅自改变以下内容：

- 布局
- 排版
- 标题层级
- 写法
- 风格
- 章节顺序

### 8.3 允许的修改范围
允许的修改仅包括：

1. 在原有章节内补充当前阶段内容
2. 新增当前阶段确实需要的新章节
3. 更新日期、阶段、默认基线等必要信息
4. 删除已明确确认废弃且必须移除的旧约束

### 8.4 禁止事项
禁止：

1. 把原文档整体改写成另一种风格
2. 把模块文档从“模块治理文件”改写成“泛项目说明书”
3. 每次更新都擅自改变标题层级与章节结构
4. 未经确认新增大段不属于本模块职责的内容

### 8.5 模板升级规则
如果未来需要升级 `app/providers/AGENTS.md` 的模板，必须先明确说明这是一次“模板升级”，并在确认后再统一应用。
在未确认是“模板升级”前，默认只允许做增量更新，不允许重写模板。

---

## 9. 修改规则

1. 不允许在 provider 层直接访问向量库
2. 不允许在 provider 层直接组织 retrieval query
3. 不允许在 provider 层生成 citations
4. 不允许让厂商原始响应直接泄漏给 services / rag
5. 不允许把 retrieval 逻辑混进 chat provider
6. 不允许在 provider 层承担 request assembly 或 context update

---

## 10. Code Review 清单

1. providers 是否仍然保持为“厂商接入层”？
2. chat / stream 是否都通过稳定抽象暴露？
3. 是否没有将 retrieval / context / citation 逻辑写进 provider 层？
4. canonical non-stream / stream contract 是否稳定？
5. `openai` / `deepseek` 与脚手架 Provider 的成熟度声明是否与代码一致？
6. 错误映射是否合理？
7. 是否没有把底层厂商响应结构直接泄漏给上层？
8. 本次文档更新是否遵守了“文档维护规则”？
9. 是否保持了原有布局、排版、标题层级、写法和风格？

---

## 11. 测试要求

至少覆盖：

1. chat provider 基础行为
2. stream provider 基础行为
3. canonical chunk / response 结构稳定性
4. timeout / error 映射
5. config 加载
6. `ProviderRegistry` 的实现态 / 脚手架态选择
7. 不同 provider 的 canonical contract 稳定性

---

## 12. 一句话总结

`app/providers/` 在当前代码基线中是系统的模型与厂商接入层，负责以统一抽象对接 chat completion 与 stream completion，并通过注册表管理已实现与脚手架 Provider，而不参与业务编排、知识检索或 citation 逻辑，并在后续更新中严格遵守模块文档的模板冻结规则。
