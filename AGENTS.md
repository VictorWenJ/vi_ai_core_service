# AGENTS.md

> 更新日期：2026-04-10

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
- 内部 `rag` 子域的治理占位与后续 Knowledge + Citation 基础能力

---

## 3. 当前项目范围

当前仍限定为八个业务/系统分层与治理域：

1. API 接入层（`app/api/`）
2. 应用编排层（`app/services/`）
3. 上下文管理层（`app/context/`）
4. Prompt 资产层（`app/prompts/`）
5. 模型 API 接入层（`app/providers/`）
6. 可观测性基础设施层（`app/observability/`）
7. 数据模型层（`app/schemas/`）
8. 知识与检索子域（`app/rag/`）

`infra/` 是项目级工程基础设施治理域，不属于第九层业务层。:contentReference[oaicite:1]{index=1}

---

## 4. 当前轮次主任务（强约束）

当前轮次为：

**Phase 6：Knowledge + Citation Layer**

### 本轮必须完成

截至当前代码基线，以下内容仍属于本轮待完成项，尚未在仓库代码中落地：

- 在 `vi_ai_core_service` 内新增 `app/rag/` 运行时代码子域
- 先作为内部能力建设，不拆独立 RAG 微服务
- 建立知识对象模型、chunk 模型、retrieval 结果模型、citation 模型
- 建立最小 ingest pipeline：
  - parser
  - cleaner
  - chunker
  - embedding
  - index
- 引入向量检索能力，并支持基础 metadata filter
- 将 retrieved knowledge block 纳入 request assembly
- `/chat` 返回 citations
- `/chat_stream` 的 `response.completed` 支持携带 citations
- 建立 retrieval observability 与基础测试闭环

### 本轮默认技术基线

- 向量数据库：**Qdrant**
- 相似度度量：**Cosine**
- embedding：先采用单一文本 embedding 基线，并通过 provider 抽象封装
- chunking：**结构感知 + token-aware + overlap**
- RAG 定位：**外部知识 grounding 与 citation，不替代 Phase 4 的短期记忆**

### 本轮明确不做

- 独立 RAG 微服务
- 大而全知识运营后台
- Agentic RAG
- 自动写回知识库
- 长期记忆平台
- 审批流
- Case Workspace
- 多模态检索主链路
- Web 爬虫平台化

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

其中：

- `api` 负责 HTTP / SSE 协议输出
- `services` 负责同步与流式会话编排
- `context` 负责会话状态与记忆收口规则
- `rag` 负责知识导入、检索、引用装配；截至当前代码基线该子域仅有治理文档占位，尚未落地运行时代码
- `providers` 负责模型厂商适配；截至当前代码基线仅实现 chat / streaming provider，embedding 尚未落地
- `schemas` 负责内部共享契约；当前 API 对外 request / response schema 位于 `app/api/schemas/`
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
截至当前代码基线，citation 契约尚未在 `/chat` 与 `/chat_stream` 中落地。

---

## 8. 当前阶段能力声明

当前阶段已实现并要求保持稳定：

- HTTP 服务化运行方式
- Phase 2 token-aware context
- Phase 3 持久化短期记忆
- Phase 4 conversation-scoped layered short-term memory
- Phase 5 Streaming Chat & Conversation Lifecycle
- Docker / compose 本地运行方式

当前代码事实补充：

- `app/rag/` 当前仅有模块治理文档占位
- `/chat` 当前未返回 citations
- `/chat_stream` 的 `response.completed` 当前未返回 citations
- `request_assembler` 当前装配顺序为：
  - system prompt
  - working memory block
  - rolling summary block
  - recent raw messages
  - current user input

当前轮次待新增：

- **Phase 6：Knowledge + Citation Layer**

当前轮次所有实现，必须严格限制在当前阶段边界内，不得提前扩展到：

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
