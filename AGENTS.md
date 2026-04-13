# AGENTS.md

> 更新日期：2026-04-13

## 1. 文档定位

本文件定义 `vi_ai_core_service` 的仓库级协作与治理规则、开发约束、文档维护规则与 review 总要求。

根目录四个文件各自承担不同职责：

- `AGENTS.md`：仓库级协作规则、治理规则、文档维护规则与开发约束
- `PROJECT_PLAN.md`：阶段规划与路线图
- `ARCHITECTURE.md`：总体架构、分层职责与依赖方向
- `CODE_REVIEW.md`：项目级审查标准与验收检查点

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
当前目标不是做“大而全”的平台，而是先把面向主流 C 端 AI 应用的核心会话后端打稳，并在此基础上逐步补齐可商用的知识增强能力。

当前阶段聚焦：

- 多模型接入
- Prompt 资产组织
- conversation-scoped 短期记忆
- 流式与非流式聊天交付
- 对外 API
- 最小可观测性
- 稳定数据契约
- 本地运行与交付（`infra/`）
- 内部 `rag` 子域的 Knowledge + Citation 运行时能力
- `chat` / `chat_stream` 统一执行骨架

---

## 3. 当前项目范围

当前仍限定为十个业务/系统分层与治理域：

1. API 接入层（`app/api/`）
2. 应用入口与 façade 层（`app/services/`）
3. Chat Runtime 执行层（`app/chat_runtime/`）
4. 上下文管理层（`app/context/`）
5. Prompt 资产层（`app/prompts/`）
6. 模型 API 接入层（`app/providers/`）
7. 可观测性基础设施层（`app/observability/`）
8. 数据模型层（`app/schemas/`）
9. 知识与检索子域（`app/rag/`）
10. 数据库基础设施层（`app/db/`）

`infra/` 是项目级工程基础设施治理域，不属于业务分层。

---

## 4. 当前轮次主任务（强约束）

当前轮次为：

**Chat Runtime 骨架收敛（先收口 `chat` / `chat_stream`，为后续能力升级留位）**

### 前置已落地基线（当前代码事实）

截至当前代码基线，以下能力已在仓库中落地并应视为本轮前置事实：

- Phase 2：token-aware context 已落地
- Phase 3：持久化短期记忆已落地
- Phase 4：conversation-scoped layered short-term memory 已落地
- Phase 5：Streaming Chat & Conversation Lifecycle 已落地
- Phase 6：Knowledge + Citation Layer 已落地
- Phase 7：RAG Evaluation + Offline Build Foundation 已基本落地
- `ChatService` 与 `StreamingChatService` 已分别承担同步与流式 chat 主链路
- `ChatRequestAssembler` 已承担 system / knowledge / memory / summary / recent raw / user 的装配中枢职责
- `/chat` 已返回 citations，`/chat_stream` completed 事件已返回 citations
- `LLMRequest` 已预留 `tools / tool_choice / response_format / attachments` 等后续能力扩展位

### 本轮目标

当前轮次聚焦在**不改变现有对外 chat contract、不过早引入 Tool Calling / Agent Runtime / 前端适配**的前提下，完成 `chat` 与 `chat_stream` 的统一执行骨架收敛。
本轮应优先补齐：

- 新增 `app/chat_runtime/` 作为聊天执行骨架层
- 把同步与流式链路的共同业务语义收口到统一 runtime
- 让 `ChatService` / `StreamingChatService` 降级为 façade / 交付入口，而不是继续承担主编排内核
- 将 workflow 显式定义为数组形式的主流程配置
- 将 lifecycle hook 显式定义为事件数组配置，并支持 step 前后 hook
- 为未来 skill 运行时预留 `workflow -> skills[]` 引用位，但当前不实现 runtime skill loader
- 统一 trace 收口，为后续可观测性与 internal console 调试页留数据基础

### 本轮默认技术基线

- 新模块命名：`app/chat_runtime/`
- 主 workflow 形式：`list[str]`
- lifecycle hook 形式：`dict[event_name, list[hook_name]]`
- step hook 形式：`dict[before_step:* | after_step:*, list[hook_name]]`
- skill 预留形式：`list[str]`
- 同步与流式共享同一套业务语义；仅交付方式不同
- `ChatRequestAssembler` 继续作为唯一 request assembly 中枢
- `ContextManager` 继续只负责 short-term memory 与 completed 收口
- `RAGRuntime` 继续只负责知识子域运行时，由 chat runtime 编排调用

### 本轮明确不做

- Tool Calling Runtime
- Agent Runtime
- Planner / Executor
- runtime policy center
- runtime skill loader
- 通用 workflow 平台化
- 多 Agent
- 前端适配与页面重构
- 长期记忆平台
- 审批流 / Case Workspace

---

## 5. 文档模板冻结规则（强约束）

根目录四个核心文档、模块级 `AGENTS.md` 与 `skill` 文件均属于项目治理模板资产。
后续任何更新都必须遵守以下规则：

### 5.1 基线规则
- 必须以当前文件内容为基线进行增量更新
- 不涉及变动的内容不得改写
- 未经明确确认，不得重写文件整体风格

### 5.2 冻结规则
未经明确确认，不得擅自改变以下内容：

- 布局
- 排版
- 标题层级
- 写法
- 风格
- 章节顺序

### 5.3 允许的修改范围
允许的修改仅包括：

1. 在原有章节内补充当前阶段内容
2. 新增当前阶段确实需要的新章节
3. 更新日期、阶段、默认基线等必要信息
4. 删除已明确确认废弃且必须移除的旧约束

### 5.4 禁止事项
禁止：

1. 把原文档整体改写成另一种风格
2. 把原本职责清晰的文件改写成职责混乱的综合说明书
3. 每次更新都擅自改变标题层级与章节结构
4. 未经确认新增不属于该文件职责的大段内容

### 5.5 模板升级规则
如果未来需要升级根目录文档模板、模块 `AGENTS.md` 模板或 `skill` 模板，必须先明确说明这是一次“模板升级”，并在确认后再统一应用。
在未确认是“模板升级”前，默认只允许做增量更新，不允许重写模板。

---

## 6. 全局依赖方向

整体业务依赖方向仍应遵守：

`api -> services -> chat_runtime -> context/prompts/rag/providers -> schemas`

数据库与存储相关基础设施依赖应通过 `app/db/` 与 `app/rag/content_store/` 收敛，不得反向污染 API 契约层。

其中：

- `api` 负责 HTTP / SSE 协议输出
- `services` 负责用户请求入口适配、同步/流式结果交付与 façade 收口
- `chat_runtime` 负责统一聊天执行骨架、workflow / hook / trace 调度
- `context` 负责会话状态与记忆收口规则
- `rag` 负责知识导入、检索、引用装配与可降级 retrieval 运行时
- `providers` 负责模型厂商适配，并提供独立 embedding provider 抽象与实现入口
- `schemas` 负责内部共享契约；当前 API 对外 request / response schema 位于 `app/api/schemas/`
- `db` 负责全项目共享数据库基础设施能力
- `observability` 负责结构化日志；当前代码核心能力为 `log_report`

任何新能力都不得破坏以上基础依赖方向。

---

## 7. 架构原则

### 7.1 根目录文档负责仓库级治理
根目录四个文件分别承担：
- 协作与治理
- 阶段规划
- 总体架构
- 审查标准

不得互相越位，不得写成一个文件包办全部职责。

### 7.2 模块文档负责模块级治理
模块 `AGENTS.md` 负责：
- 模块职责
- 模块边界
- 模块结构
- 局部 review 标准
- 局部测试要求

### 7.3 skill 负责执行型约束
skill 用于约束在模块内“如何做事”，而不是重新定义仓库级治理规则。

### 7.4 retrieval 不替代 short-term memory
Phase 6 中引入的知识增强能力，不得替代 Phase 4 已建立的：
- recent raw
- rolling summary
- working memory

### 7.5 citation 是本轮一等能力
citation 必须来自 retrieval 结果，不得变成模型自由生成的装饰性文本。
截至当前代码基线，citation 契约已在 `/chat` 与 `/chat_stream` completed 中落地。

### 7.6 中文字段注释与默认配置说明规则

为提高当前代码基线的可读性、可维护性与后续协作稳定性，仓库内新增以下强约束：

1. 所有使用 `@dataclass` 定义的类，其每一个字段都必须补充中文注释，说明字段含义；如字段存在单位、取值语义、是否可空、默认行为或生命周期语义，也必须在注释中明确。
2. 所有项目级默认配置常量（如 `DEFAULT_*`）都必须补充中文注释，说明配置项含义、作用范围与默认行为；涉及 token、chars、seconds、ttl、size、top-k、threshold 等数值时，必须写明单位或语义。
3. 上述中文注释属于项目级可维护性资产。除非对应字段或配置项被明确删除，否则后续任何改动不得删除、不得改写为英文、不得在重构或格式化过程中丢失。
4. 当字段名、默认值、单位、语义或使用边界发生变化时，必须同步更新对应中文注释，不允许出现“代码已变、注释未变”的漂移。
5. 本规则适用于 `app/config.py`、各模块 `models.py`、`schemas`、`services` 中的 dataclass 对象，以及其他承担结构化数据表达职责的 dataclass 文件。

---

### 7.7 Chat Runtime 收敛规则

`chat` 与 `chat_stream` 的核心业务语义必须逐步收口到 `app/chat_runtime/`，不得继续在 `ChatService` 与 `StreamingChatService` 中形成双编排内核。

要求：

1. `app/services/` 保持 façade / 入口适配定位。
2. `app/chat_runtime/` 负责 workflow、hook、step dispatch、trace 收口。
3. workflow 主流程必须显式声明，不得继续依赖散落的大函数隐式顺序。
4. hook 必须与主 workflow 分离配置，禁止把 lifecycle hook 与主步骤混成同一个数组。
5. 当前阶段只允许做 chat runtime 骨架，不得借机做 Tool Calling / Agent Runtime 平台化。

---

### 7.8 API 控制面命名收敛规则

控制面 API 与其路由文件应按**领域职责**命名，而不是按当前消费者命名。
当前阶段要求：

1. `app/api/` 中的路由文件应统一按领域命名，例如：`chat.py`、`knowledge.py`、`evaluation.py`、`runtime.py`。
2. 不再保留以 `*_console.py` 命名的正式 API 模块名；“console”只能描述当前消费者，不能定义后端领域能力命名。
