# ARCHITECTURE.md

> 更新日期：2026-04-06


## 1. 文档定位

本文件定义 `vi_ai_core_service` 的项目级总体架构。

本文件只描述仓库层面的系统分层、职责划分、依赖方向、调用关系与演进原则，  
不展开到各模块的内部详细设计。  
模块内部设计应在对应模块的本地文档中定义。

---

## 2. 架构目标

本项目总体架构目标如下：

1. 建立边界清晰的 AI 服务分层结构
2. 让不同能力在不同目录中各司其职
3. 让模型接入、Prompt、Context、编排、API 暴露彼此分离
4. 让系统在后续新增 RAG / Agent / Tool 等能力时具备可扩展性
5. 让协作者与 Codex 能快速判断代码应该落在哪一层

---

## 3. 当前总体架构分层

当前系统按以下七层组织：

### 3.1 API 接入层
对应目录：`app/api/`

职责：

- 暴露 HTTP 接口
- 接收请求
- 做基础输入校验
- 调用应用编排层
- 返回标准响应

### 3.2 应用编排层
对应目录：`app/services/`

职责：

- 串联系统能力模块
- 承接业务用例级流程
- 组织一次完整调用链
- 协调 Context / Prompt / Provider

### 3.3 上下文管理层
对应目录：`app/context/`

职责：

- 管理会话上下文
- 表示历史消息
- 提供上下文管理入口
- 抽象上下文存储
- 承接上下文窗口选择、截断与序列化策略

### 3.4 Prompt 资产层
对应目录：`app/prompts/`

职责：

- 管理 Prompt 模板资产
- 提供模板注册与查找
- 提供渲染能力
- 支撑多场景 Prompt 演进

### 3.5 模型 API 接入层
对应目录：`app/providers/`

职责：

- 对接不同模型厂商
- 屏蔽厂商协议差异
- 提供统一 provider 抽象
- 管理 provider 注册与发现
- 归一化模型结果

### 3.6 可观测性基础设施层
对应目录：`app/observability/`

职责：

- 提供统一 logging 初始化能力
- 约束统一日志前缀输出（`<time> <level> [<thread>] <logger> <file>:<line> event=<event>`）
- 约束业务日志体输出（`message=<json>`）
- 提供 request context 字段贯穿规则
- 提供 exception logging 基础能力
- 为 API / services / providers 提供通用日志事件支持

说明：

- 本层是横切基础设施层，不承载业务流程
- 当前阶段只做 logging/request context/exception logging 基础设施，不做 tracing/metrics/alerting 平台化建设
- 当前阶段业务 payload 默认可输出（调试优先），由 `.env` 开关控制
- 凭据字段（如 API key、Authorization）必须禁止输出

### 3.7 数据模型层
对应目录：`app/schemas/`

职责：

- 定义共享数据契约
- 定义请求模型与响应模型
- 为跨层协作提供稳定数据表示

---

## 4. 总体依赖方向

项目总体依赖方向如下：

`api -> services -> context/prompts/providers -> schemas`

同时：

- `observability` 作为横切基础设施层，可被 `api/services/providers` 等层依赖
- `observability` 不反向依赖业务编排实现（不得依赖 `api/services/providers` 的业务流程逻辑）

### 解释

- `api` 依赖 `services`，但不直接承担底层能力实现
- `services` 调用 `context/prompts/providers` 完成用例级编排
- `context/prompts/providers` 各自提供专项能力
- `observability` 提供横切日志与上下文字段能力
- `schemas` 被多个层复用，作为共享契约层

### 运行入口约束（当前阶段）

- 唯一运行入口是 `app/server.py`（FastAPI HTTP 服务）
- 对外调用方式是 HTTP 路由（如 `/health`、`/chat`）
- 当前阶段不保留 CLI 直接调用入口

---

## 5. 总体调用关系

当前系统的典型调用思路应为：

1. 外部请求进入 API 层
2. API 层将请求委托给应用编排层
3. 应用编排层根据需要：
   - 获取/组装 Context
   - 获取/渲染 Prompt
   - 调用 Provider 发起模型请求
   - 调用 Observability 记录结构化事件与异常信息
4. Provider 返回归一化结果
5. Service 整理结果并返回 API 层
6. API 层输出稳定响应

这条主链路是当前项目的核心调用路径。

## 5.1 Context Engineering Phase 1 调用链补充

在当前阶段，服务端上下文治理采用以下调用链：

`api -> services/chat_service.py -> services/request_assembler.py -> context/manager.py -> context/stores/* -> context/policies/* -> services/request_assembler.py -> providers/*`

### 设计说明

1. `app/context/` 负责：
   - 定义 canonical context models
   - 读取原始 session history
   - 抽象存储后端
   - 承接 history selection / truncation / serialization policy

2. `app/services/request_assembler.py` 负责：
   - 解析当前请求的上下文模式
   - 从 context 层获取历史
   - 驱动上下文策略执行
   - 将系统 prompt、历史消息、当前用户输入装配为最终 `LLMRequest.messages`

3. `app/services/chat_service.py` 负责：
   - 调用 request assembler
   - 调用 provider
   - 处理主链路异常传播
   - 在响应完成后回写新消息到 context 层

### 架构边界

- context 层不负责最终 prompt 装配顺序
- context 层不负责 provider 请求格式
- request assembler 不直接依赖具体 store 实现
- chat service 不直接承载 history selection / truncation 细节

---

## 6. 分层设计原则

### 6.1 单层单责

每一层应只承载自身主要职责：

- API 层负责接入
- Service 层负责编排
- Provider 层负责模型适配
- Prompt 层负责模板资产
- Context 层负责上下文治理
- Observability 层负责可观测性基础设施
- Schema 层负责契约定义

### 6.2 下层不反向感知上层

底层模块不应依赖上层编排或 API 细节。  
例如：

- `providers` 不应依赖 `services`
- `context` 不应依赖 `api`
- `schemas` 不应依赖任何业务层

### 6.3 专项能力横向分离

Prompt、Context、Provider 应视为平行专项能力，而不是相互嵌套的附属工具模块。

### 6.4 共享契约稳定

Schema 层必须尽量保持稳定，否则会影响多个层的协作与演进。

---

## 7. 根目录与模块目录的架构关系

本项目的架构文档采用两级治理：

### 根目录架构文档负责

- 定义系统总体层次
- 定义依赖方向
- 定义跨模块架构原则
- 定义新增模块的纳入标准

### 模块级文档负责

- 定义本模块内部结构
- 定义本模块内的抽象边界
- 定义本模块未来局部演进方式
- 定义本模块的详细 review 关注点

即：

- 根目录讲“整个系统怎么分”
- 模块文档讲“这个模块内部怎么做”

---

## 8. 当前目录与架构映射

当前项目目录应按以下方式理解：

- `app/`：主应用代码根目录
- `app/api/`：外部接口接入层
- `app/services/`：应用编排层
- `app/context/`：上下文能力模块
- `app/prompts/`：Prompt 资产模块
- `app/providers/`：模型接入适配模块
- `app/observability/`：可观测性基础设施模块
- `app/schemas/`：共享数据契约模块
- `tests/`：测试验证层
- `skills/`：后续独立治理，不属于当前主架构说明重点

---

## 9. 当前架构边界约束

当前系统必须遵守以下架构边界：

1. API 层不得成为业务逻辑堆积层
2. Service 层不得成为 provider 适配层
3. Provider 层不得承担业务主流程
4. Prompt 层不得承担业务控制流
5. Context 层不得承担模型调用
6. Context 层不得承担最终 prompt 装配顺序
7. Observability 层不得承担业务流程或 provider 接入逻辑
8. Schema 层不得承担业务逻辑

只要这几条边界被破坏，系统复杂度就会快速上升。

---

## 10. 可扩展架构原则

当前架构不是最终形态，但必须为后续扩展留出空间。

未来潜在扩展方向包括：

- `app/rag/`
- `app/agents/`
- `app/tooling/`
- `app/evaluation/`
- 更细化的 contracts
- integration tests / e2e tests

这些新模块进入项目时，必须满足：

1. 与现有层职责不重复
2. 能解释清楚依赖方向
3. 不破坏当前七层主结构（含 observability 横切层）
4. 有相应模块级文档约束

### Context 与 RAG 的未来边界约束

未来若引入 `app/rag/`，其职责应是“额外上下文来源与检索增强”，而不是替代 `app/context/` 作为会话历史主真相源。

原则上：

- `app/context/` 负责 conversation/session history
- `app/rag/` 负责 knowledge retrieval / grounding
- 两者都可为 request assembly 提供上下文，但职责不同、边界不可混淆

---

## 11. 当前架构优先保证什么

当前阶段，架构最优先保证的是：

- 分层正确
- 调用链清晰
- 模块不混写
- Provider / Prompt / Context 三类能力正确分离
- Observability 作为横切基础设施层边界清晰
- Schema 作为共享契约保持稳定
- 文档治理与代码结构一致
- request assembly 中的上下文治理路径稳定、明确、可测试

### 当前阶段实现基线（强约束）

- 本阶段已实现并验收：
  - 单轮非流式 LLM 主链路
  - provider/prompt/context 的基础设施骨架
  - 可回归的最小测试集
- 本阶段正在增强并要求边界正确：
  - short-term conversation history governance
  - 最近 N 轮 window selection
  - truncation placeholder
  - history serialization pipeline
  - request assembly 中的上下文装配治理
- 本阶段仅预留，不要求落地：
  - streaming 真正实现
  - 多模态真实处理链路
  - tools/function calling 与 structured output 真正能力
  - persistence / summary / semantic recall
  - RAG retrieval pipeline
  - 新系统层与重平台化改造

---

## 12. 当前架构暂不追求什么

当前阶段暂不追求：

- 过细粒度的子系统拆分
- 复杂的通用插件化平台
- 尚无明确需求的高级抽象
- 过早引入大量未来能力目录
- 把 Context Engineering Phase 1 直接扩展成 memory platform

当前最重要的是“正确基础”，不是“看起来很大很全”。

---

## 13. 一句话总结

`vi_ai_core_service` 当前采用 **七层治理式 AI 服务架构**：  
以 API 接入为入口，以应用编排为中枢，以 Context / Prompt / Provider 为专项能力模块，以 Observability 作为横切基础设施层，以 Schema 为稳定契约层，从而为后续更复杂 AI 系统能力扩展打基础。

在 Context Engineering Phase 1 中，重点是把“服务端历史如何进入一次模型请求”收敛为正式架构路径。

---

## 14. 架构治理执行顺序（新增）

架构执行上，必须先做“治理链路”再做“实现细节”：

1. 项目级约束：根目录四文档
2. 模块级约束：目标模块 `AGENTS.md`
3. 任务级做法：对应 skill 文档
4. 代码实现：仅在分层边界内落地
5. 架构审查：按 `CODE_REVIEW.md` 做边界与依赖检查
6. 文档回写：保持文档事实与代码现实一致

该顺序不是建议，而是架构门禁。任何跳过步骤的改动都视为高风险改动。

### Context Engineering Phase 1 专项执行顺序

1. 先定义 context history 的 canonical model
2. 再定义 selection / truncation / serialization policy 接口
3. 再确定 `request_assembler.py` 的装配职责
4. 最后再接入主链路与测试

不允许先写历史拼接逻辑、后补边界说明。
