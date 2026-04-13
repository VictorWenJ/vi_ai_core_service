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

---

## 3. 当前项目范围

当前仍限定为九个业务/系统分层与治理域：

1. API 接入层（`app/api/`）
2. 应用编排层（`app/services/`）
3. 上下文管理层（`app/context/`）
4. Prompt 资产层（`app/prompts/`）
5. 模型 API 接入层（`app/providers/`）
6. 可观测性基础设施层（`app/observability/`）
7. 数据模型层（`app/schemas/`）
8. 知识与检索子域（`app/rag/`）
9. 数据库基础设施层（`app/db/`）

`infra/` 是项目级工程基础设施治理域，不属于业务分层。

---

## 4. 当前轮次主任务（强约束）

当前轮次为：

**RAG 持久化控制面升级（Post-Phase 7 主线）**

### 前置已落地基线（当前代码事实）

截至当前代码基线，以下能力已在仓库中落地并应视为本轮前置事实：

- Phase 2：token-aware context 已落地
- Phase 3：持久化短期记忆已落地
- Phase 4：conversation-scoped layered short-term memory 已落地
- Phase 5：Streaming Chat & Conversation Lifecycle 已落地
- Phase 6：Knowledge + Citation Layer 已落地
- Phase 7：RAG Evaluation + Offline Build Foundation 已基本落地
- `app/providers/` 已按 `chat/` 与 `embeddings/` 分层
- API 文件命名已从 `*_console.py` 收敛为领域命名（`knowledge.py`、`evaluation.py`、`runtime.py`）
- `app/rag/console_service.py` 已拆分，不再保留大而全控制台服务
- LangChain document loader 已按“受控适配层”方式引入，不接管内部 RAG 主链路
- `app/api/schemas/` 已明确用于集中 API request / response contract
- 当前 `app/rag/state.py` 与 `app/api/deps.py` 仍以进程内 `RAGControlState` 承担正式控制面事实，这正是本轮要替换的对象

### 本轮目标

当前轮次聚焦在**不破坏 Phase 6 / Phase 7 在线能力与 Internal Console v1 现有页面范围**的前提下，完成 RAG 控制面的正式持久化升级。
本轮应优先补齐：

- 删除 `RAGControlState` 作为正式控制面真相源
- 新增 `app/db/` 作为全项目共享数据库基础设施层
- 在 `app/rag/` 内引入 `repository/` 持久化访问层与 `content_store/` 内容存储层
- 以 MySQL 持久化以下控制面对象：
  - `documents`
  - `document_versions`
  - `build_tasks`
  - `build_documents`
  - `chunks`
  - `evaluation_runs`
  - `evaluation_cases`
- 以文件系统 / 对象存储保存：
  - 原始上传文件
  - normalized text 快照
- 继续使用 Qdrant 负责：
  - embeddings
  - vector payload
  - vector retrieval
- 将 build 的输入快照收敛为 `manifest_details`
- 将 evaluation run / case 结果改为全量持久化，而不是仅保留运行时态
- 将 Inspector 的“查看向量详情”能力收敛为按 `vector_point_id` 从 Qdrant 回读，而不是在 MySQL 冗余存整段向量

### 本轮默认技术基线

- 控制面数据库：**MySQL**
- 向量数据库：**Qdrant**
- 内容存储：先采用**本地文件系统 / 简单对象存储风格目录**
- 相似度度量：**Cosine**
- embedding：单一文本 embedding 基线，并通过 provider 抽象封装
- chunking：**结构感知 + token-aware + overlap**
- 结构化字段命名：优先使用业务语义命名，详情对象使用 `*_details`，标识集合使用 `*_ids`
- API 契约边界：`app/api/schemas/` 仅承载对外 request / response contract；领域内部对象保留在各自模块内
- repository 标准化：核心持久化查询结果不得长期以裸 `dict` 对外暴露；每张核心表应有明确的持久化实体对象，并通过 mapper 转换为领域对象或专用 read model

### 本轮明确不做

- 异步任务系统（queue / worker / thread pool）
- 审计平台
- 多租户 / 权限体系
- 复杂对象存储平台化
- 独立 RAG 微服务
- 用 MySQL 替换 Qdrant
- 让 LangChain 或其他框架接管内部 RAG 主链路
- Tool Calling / Agent Runtime
- Case Workspace / 审批流
- 多模态检索主链路
- 跨 MySQL / 文件存储 / Qdrant 的强分布式事务体系

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

`api -> services -> context/prompts/rag/providers -> schemas`

数据库与存储相关基础设施依赖应通过 `app/db/` 与 `app/rag/content_store/` 收敛，不得反向污染 API 契约层。

其中：

- `api` 负责 HTTP / SSE 协议输出
- `services` 负责同步与流式会话编排
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



### 7.7 API 控制面命名收敛规则

控制面 API 与其路由文件应按**领域职责**命名，而不是按当前消费者命名。
当前阶段要求：

1. `app/api/` 中的路由文件应统一按领域命名，例如：`chat.py`、`knowledge.py`、`evaluation.py`、`runtime.py`。
2. 不再保留以 `*_console.py` 命名的正式 API 模块名；“console”只能描述当前消费者，不能定义后端领域能力命名。
3. API schema、API client、前端页面与测试用例后续也应跟随后端领域命名收敛，不长期维持“领域名 + console 后缀”双轨。
4. 控制台只是当前消费者，后端 API 命名必须保持可被未来正式产品前端、CLI、集成测试与其他服务复用的中性命名。

### 7.8 文档加载器引入原则
### 7.9 控制面持久化升级原则

文档加载器属于知识接入适配能力，不属于本项目当前阶段必须手搓的核心竞争力。
当前阶段允许在 `app/rag/ingestion/` 中引入成熟文档加载器框架作为 loader adapter，例如 LangChain document loaders，但必须遵守：

1. 只允许 loader 层借助成熟框架，不允许让外部框架接管内部 `KnowledgeDocument` / `KnowledgeChunk` / `Citation` 等领域模型。
2. clean / normalize / chunking / metadata enrichment / build version / retrieval / citation 仍由仓库内部代码主导。
3. loader adapter 的输出必须先转换为本项目内部中间表示，再进入现有 ingest pipeline。
4. 不允许因为引入 loader 框架而把 `app/rag/` 重构成 LangChain 主导的端到端 RAG 流水线。

### 7.9 控制面持久化升级原则
- MySQL 负责控制面与治理数据，不负责向量检索
- Qdrant 继续负责 embeddings、payload 与 retrieval
- 文件存储负责原始文件与 normalized text 快照
- `RAGControlState` 不得继续作为正式控制面
- `repository` 负责持久化访问封装，不得在 API / service 中散落 SQL
- 本轮允许同步执行 build / evaluation，但相关对象必须按“任务对象”落表

## 8. 当前阶段能力声明

当前阶段已实现并要求保持稳定：

- HTTP 服务化运行方式
- Phase 2 token-aware context
- Phase 3 持久化短期记忆
- Phase 4 conversation-scoped layered short-term memory
- Phase 5 Streaming Chat & Conversation Lifecycle
- Docker / compose 本地运行方式

当前代码事实补充：

- `app/rag/` 已落地运行时代码与最小 ingest/retrieval 闭环
- `/chat` 已返回 `citations`（为空时返回空数组）
- `/chat_stream` 的 `response.completed` 已返回 `citations`
- `request_assembler` 当前装配顺序为：
  - system prompt
  - knowledge block
  - working memory block
  - rolling summary block
  - recent raw messages
  - current user input

当前轮次新增（本轮已落地）：

- RAG 评估数据集主表与标签集（query / retrieval / citation / answer 分层标签）
- retrieval / citation / answer benchmark runner 与结构化评估结果输出
- 离线构建元数据与构建批次概念（build_id / version_id / chunk_strategy_version / embedding_model_version）
- 增量构建与局部重建约束（manifest + 内容哈希）
- 基础质量门禁与构建统计（failure ratio / empty chunk ratio / upsert 一致性）
- Internal Console v1 已落地，并通过领域化控制面 API 消费 knowledge / evaluation / runtime 能力
- API 路由文件已按领域命名收敛为 `chat.py`、`knowledge.py`、`evaluation.py`、`runtime.py`
- `app/rag/console_service.py` 已拆分为 `document_service.py`、`build_service.py`、`inspector_service.py`、`evaluation_service.py`
- runtime summary / config / health 聚合能力已落位 `app/services/runtime_service.py`
- 文档加载器已在 `app/rag/ingestion/loaders/` 引入受控 adapter（含 LangChain PyMuPDF loader 适配）

当前轮次所有实现，必须严格限制在当前阶段边界内，不得提前扩展到：

- Tool Calling / Action Layer
- 长期记忆平台
- 审批流
- Case Workspace
- Agent Runtime
- 多模态检索主链路

---

## 9. 修改规则

1. 不允许绕过根目录四文档与模块 `AGENTS.md` 直接开展无边界实现
2. 不允许在未更新治理文档的前提下擅自扩大模块职责
3. 不允许把你和用户之间的协作流程写入本文件作为 Codex 约束
4. 不允许在仓库级文档中混入不属于当前文件职责的实现细节
5. 不允许破坏既定分层、既定阶段边界与既定模板风格

---

## 10. Code Review 总要求

在进入具体模块 Review 前，至少先确认：

1. 是否遵守了当前阶段边界？
2. 是否遵守了文档模板冻结规则？
3. 是否保持了根目录四文档各自职责清晰？
4. 是否有跨层绕过、职责漂移、边界膨胀？
5. 是否补了必要测试？
6. 是否破坏了同步与流式主链路？
7. 若声称落地了 citation、retrieval、chunking、embedding 等 Phase 6 关键能力，是否真的已有代码、测试与可回归依据，而不是只停留在文档描述？

---

## 11. 一句话总结

`AGENTS.md` 在当前阶段的职责，是作为仓库级治理总纲，明确项目定位、阶段主任务、文档模板冻结规则、全局依赖方向、架构原则与仓库级开发约束，用于约束实现代理行为，而不承担用户与助手之间的交互流程说明职责。
