# app/schemas/AGENTS.md

> 更新日期：2026-04-10

## 1. 文档定位

本文件定义 `app/schemas/` 的职责、边界、结构约束、开发约束与 review 标准。  
当前阶段，本文件临时同时承担该模块的 `AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW` 职责。  
执行 schemas 相关任务时，必须先读根目录 `AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md`，再读本文件，再根据 skill `skills/python-schema-capability/` 执行。

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

`app/schemas/` 是系统的共享契约层。  
它负责定义同步请求、同步响应、流式事件、取消、重置、lifecycle、citation 以及其他跨模块共享的数据契约。

一句话：**schemas 层负责“系统对内对外共享的数据结构如何表达”。**

当前阶段建议围绕以下职责组织：

- `/chat` request / response schemas
- `/chat_stream` 事件 payload schemas
- `/chat_stream_cancel` request / response schemas
- `/chat_reset` request / response schemas
- lifecycle 相关 schemas
- citation 相关 schemas
- 其他跨模块共享 contract

---

## 3. 本模块职责

1. 定义 API request / response 契约
2. 定义 stream event payload 契约
3. 定义 cancel / reset 契约
4. 定义 message lifecycle 相关共享数据契约
5. 在 Phase 6 中定义 citation 相关共享数据契约
6. 保持对外 contract 清晰、稳定、可演进
7. 为各模块提供统一的数据表达基础

---

## 4. 本模块不负责什么

1. 不负责 HTTP 路由
2. 不负责 chat 主链路编排
3. 不负责 context store 实现
4. 不负责 provider SDK 适配
5. 不负责 retrieval / chunking / embedding / index 实现
6. 不负责 citation 生成逻辑
7. 不负责业务状态推进

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

### 6.1 契约优先
系统对内对外的数据表达，必须先有清晰 schema，再进入 API / service / provider / rag 的实现。

### 6.2 向后兼容优先
已有 request / response / stream event contract 不应在无明确阶段确认下随意破坏。

### 6.3 contract 不泄漏内部实现细节
不应直接把以下内容暴露进外部契约：

- 向量库内部结构
- embedding 维度
- provider 厂商原始响应对象
- retrieval 内部对象
- context store 内部状态细节

### 6.4 citation 是共享契约的一部分
Phase 6 后，citation 不是临时拼接字段，而是正式共享契约的一部分。

### 6.5 同步与流式契约要有一致语义
`/chat` 与 `/chat_stream` 不一定字段完全相同，但它们的核心语义必须对齐，而不是形成两套彼此冲突的表达。

---

## 7. 当前阶段能力声明

当前本轮必须保持稳定：

- `/chat` request / response contract
- `/chat_stream` started / delta / completed / error / cancelled / heartbeat event contract
- `/chat_stream_cancel` request / response contract
- `/chat_reset` request / response contract
- message lifecycle 相关字段语义

当前本轮新增要求：

- citation schema
- `/chat` response 中的 citations 字段
- `/chat_stream` completed 事件中的 citations 字段

当前本轮不要求：

- 全量业务对象体系
- tool calling contract 全家桶
- case object contract
- 多模态 payload contract
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

1. 不允许无 schema 地新增对外字段
2. 不允许让 API、services、providers、rag 各自临时拼装不同风格的同类 contract
3. 不允许把内部 retrieval 结果对象直接透传给客户端
4. 不允许把 provider 原始响应结构直接暴露到共享契约中
5. 不允许在 delta 阶段混入 citations
6. citation 字段命名必须清晰、稳定、可读

---

## 10. Code Review 清单

1. schemas 是否仍然只是“共享契约层”？
2. `/chat` 是否定义了稳定的 citations 结构？
3. `/chat_stream` completed 事件是否定义了稳定的 citations 结构？
4. cancel / reset contract 是否清晰？
5. lifecycle 相关字段语义是否一致？
6. 是否没有泄漏底层向量库和 embedding 细节？
7. 是否保持与流式 / 非流式契约兼容？
8. 本次文档更新是否遵守了“文档维护规则”？
9. 是否保持了原有布局、排版、标题层级、写法和风格？

---

## 11. 测试要求

至少覆盖：

1. `/chat` request / response schema 结构正确
2. `/chat_stream` 事件 schema 结构正确
3. `/chat_stream_cancel` contract 结构正确
4. `/chat_reset` contract 结构正确
5. citation schema 结构正确
6. delta 阶段无 citations
7. citation 为空时行为明确
8. 现有 schema 回归不被破坏

---

## 12. 一句话总结

`app/schemas/` 在当前阶段是系统的共享契约层，负责统一定义同步、流式、取消、重置、lifecycle 与 Phase 6 citation 的共享数据表达，确保系统各层在使用同一语义时拥有一致、稳定、可演进的 contract，并在后续更新中严格遵守模块文档的模板冻结规则。