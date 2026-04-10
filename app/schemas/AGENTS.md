# app/schemas/AGENTS.md

> 更新日期：2026-04-10

## 1. 文档定位

本文件定义 `app/schemas/` 的职责、边界、结构约束、开发约束与 review 标准。
当前阶段，本文件临时同时承担该模块的 `AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW` 职责。
执行 schemas 相关任务时，必须先读根目录 `AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md`，再读本文件，再根据 skill `skills/python-schemas-capability/` 执行。

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

`app/schemas/` 是系统的内部规范化 LLM 契约层。
它负责定义 service 与 provider 之间共享的规范化请求、响应与流式 chunk 数据结构。

一句话：**schemas 层负责“内部 LLM 访问契约如何表达”。**

当前阶段建议围绕以下职责组织：

- `llm_request.py`：`LLMMessage`、`LLMRequest`
- `llm_response.py`：`LLMUsage`、`LLMResponse`、`LLMStreamChunk`
- `__init__.py`：统一导出

补充说明：

- API 层请求 / 响应模型当前位于 `app/api/schemas/chat.py`
- `app/schemas/` 当前不承载 `/chat`、`/chat_stream`、cancel、reset 或 citation 对外契约

---

## 3. 本模块职责

1. 定义 `LLMMessage`
2. 定义 `LLMRequest`
3. 定义 `LLMUsage`
4. 定义 `LLMResponse`
5. 定义 `LLMStreamChunk`
6. 保持 provider / service 共享 contract 清晰、稳定、可演进
7. 为内部 LLM 调用链提供统一的数据表达基础

---

## 4. 本模块不负责什么

1. 不负责 HTTP 路由
2. 不负责 API request / response 与 SSE 事件契约
3. 不负责 chat 主链路编排
4. 不负责 context store 实现
5. 不负责 provider SDK 适配
6. 不负责 retrieval / chunking / embedding / index 实现
7. 不负责 citation 生成逻辑与业务状态推进

---

## 5. 依赖边界

### 允许依赖
- 标准库
- 轻量数据建模工具（如当前项目使用的 schema / dataclass / pydantic 能力）
- 自身模块

### 不建议依赖
- `app/api/`
- `app/services/`
- `app/context/`
- `app/providers/`
- `app/rag/`

### 原则
schemas 是被各层依赖的共享契约层，不反向依赖业务实现层。

---

## 6. 架构原则

### 6.1 内部 canonical contract 优先
provider 与 service 之间的共享数据表达，必须先有清晰 schema，再进入具体实现。

### 6.2 向后兼容优先
已有 request / response / stream event contract 不应在无明确阶段确认下随意破坏。

### 6.3 contract 不泄漏内部实现细节
不应直接把以下内容暴露进内部共享契约：

- 向量库内部结构
- embedding 维度
- provider 厂商原始响应对象
- retrieval 内部对象
- context store 内部状态细节

### 6.4 API 契约与内部契约分离
- `/chat`、`/chat_stream`、cancel、reset 当前属于 `app/api/schemas/`
- `app/schemas/` 当前只承载内部 `LLM*` dataclass 契约
- 如未来确有跨层共享需求，必须先说明边界，再新增模型

### 6.5 同步与流式内部契约要有一致语义
`LLMResponse` 与 `LLMStreamChunk` 不要求字段完全相同，但 finish_reason、usage、metadata 等核心语义必须对齐。

---

## 7. 当前阶段能力声明

当前本轮必须保持稳定：

- `LLMMessage`
- `LLMRequest`
- `LLMUsage`
- `LLMResponse`
- `LLMStreamChunk`
- `LLMRequest` 中 provider / model / system_prompt / metadata 等字段语义

当前代码事实补充：

- API request / response contract 当前不在本模块
- citation schema 当前不在本模块，也未在仓库代码中落地
- `LLMStreamChunk` 当前定义在 `llm_response.py`，而不是独立文件

当前本轮不要求：

- `/chat` request / response
- `/chat_stream` 事件 payload
- cancel / reset contract
- citation contract
- 长期记忆对象体系

---

## 8. 文档维护规则（强约束）

本文件属于 `app/schemas/` 模块的治理模板资产。
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
如果未来需要升级 `app/schemas/AGENTS.md` 的模板，必须先明确说明这是一次“模板升级”，并在确认后再统一应用。
在未确认是“模板升级”前，默认只允许做增量更新，不允许重写模板。

---

## 9. 修改规则

1. 不允许无 schema 地新增内部共享字段
2. 不允许把 `app/api/schemas/` 与 `app/schemas/` 的职责混写
3. 不允许把 provider 原始响应结构直接暴露到共享契约中
4. 不允许把内部 retrieval 结果对象塞进当前 `LLM*` 契约
5. 不允许随意拆散 `LLMRequest` / `LLMResponse` / `LLMStreamChunk` 的统一语义
6. 如未来新增新模型，命名必须清晰、稳定、可读

---

## 10. Code Review 清单

1. schemas 是否仍然只是内部共享契约层？
2. `LLMMessage` / `LLMRequest` / `LLMResponse` / `LLMStreamChunk` 语义是否清晰？
3. 是否没有把 API 对外契约误放进 `app/schemas/`？
4. finish_reason / usage / metadata 等字段语义是否一致？
5. 是否没有泄漏底层向量库和 embedding 细节？
6. 是否保持与流式 / 非流式内部契约兼容？
7. 本次文档更新是否遵守了“文档维护规则”？
8. 是否保持了原有布局、排版、标题层级、写法和风格？

---

## 11. 测试要求

至少覆盖：

1. `LLMMessage` 初始化与角色校验
2. `LLMRequest` 字段归一化
3. `temperature` / `max_tokens` 校验
4. `LLMResponse` / `LLMUsage` 结构稳定
5. `LLMStreamChunk` 字段语义稳定
6. provider / service / request assembler 对现有 schema 的回归不被破坏

---

## 12. 一句话总结

`app/schemas/` 在当前代码基线中是系统的内部规范化 LLM 契约层，负责统一定义 provider 与 service 之间共享的 `LLM*` 数据表达，而不承接 API 对外契约、cancel / reset 或 citation 模型，并在后续更新中严格遵守模块文档的模板冻结规则。
