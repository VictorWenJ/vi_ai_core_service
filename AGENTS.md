# AGENTS.md

> 更新日期：2026-04-08

## 1. 文档定位

本文件用于定义 `vi_ai_core_service` 仓库级别的协作规则、工程边界、开发原则与文档治理方式。  
它是本项目的顶层协作文档。

本文件不替代模块级文档。  
当开发者、协作成员或 Codex 需要修改某个具体模块时，必须按以下顺序阅读文档：

1. 根目录 `AGENTS.md`
2. 根目录 `PROJECT_PLAN.md`
3. 根目录 `ARCHITECTURE.md`
4. 根目录 `CODE_REVIEW.md`
5. 目标模块目录下的 `AGENTS.md`
6. 对应 skill 文档与 checklist / test matrix / boundary 文档

---

## 2. 项目定位

`vi_ai_core_service` 是 VI AI Project 中的 Python AI 子系统。

当前阶段，本仓库聚焦于以下能力：

- 大模型 API 接入
- Prompt 资产组织与渲染
- 上下文管理与短期记忆治理
- AI 请求编排
- 对外 API 暴露
- 可观测性基础设施治理
- AI 能力相关的数据契约管理

本仓库不是“大而全”的业务系统，而是整个项目中的 Python 侧 AI 核心服务。

---

## 3. 当前项目范围

当前版本仍限定为以下七层：

1. API 接入层（`app/api/`）
2. 应用编排层（`app/services/`）
3. 上下文管理层（`app/context/`）
4. Prompt 资产层（`app/prompts/`）
5. 模型 API 接入层（`app/providers/`）
6. 可观测性基础设施层（`app/observability/`）
7. 数据模型层（`app/schemas/`）

其中 `app/observability/` 为横切基础设施模块，当前负责统一日志上报入口（`log_until.py`）与日志输出格式约束，不承担业务流程编排。

未来如果需要新增 `app/rag/`、`app/agents/` 等新层，必须在项目级文档中正式纳入并同步定义边界。

---

## 4. 项目级治理原则

### 4.1 文档分层治理

本仓库采用“文档分层治理”模式：

- 根目录文档只负责项目总体规则
- 模块目录文档只负责模块自身规则
- 根目录文档不得越权写模块内部实现细节
- 模块文档不得突破项目总体原则

### 4.2 边界清晰优先

每个目录、每一层都必须有明确职责。  
不允许无边界混合以下逻辑：

- 路由逻辑
- 编排逻辑
- Provider 适配逻辑
- Prompt 逻辑
- Context 逻辑
- Observability 基础设施逻辑
- Schema 契约逻辑

### 4.3 渐进式演进优先于过度设计

项目允许演进，但不接受没有实际需求支撑的提前抽象。  
当前阶段优先保证：

- 结构清晰
- 调用链清晰
- 模块边界稳定
- 代码与文档一致
- 可测试、可回归

### 4.4 可替换、可维护、可扩展

本项目应尽量具备以下特征：

- 抽象合理
- 依赖方向清晰
- 底层实现可替换
- 上层调用稳定
- 模块之间低耦合

### 4.5 AI 工程能力是核心能力

在本仓库中：

- Prompt
- Context
- Provider
- Observability
- 模型调用契约

都属于核心工程组成部分，而不是零散辅助代码。

---

## 5. 全局依赖方向

本仓库整体上应遵守如下依赖方向：

`api -> services -> context/prompts/providers -> schemas`

更准确地说：

- `api` 负责接收请求并转发
- `services` 负责用例级编排
- `context/prompts/providers` 负责提供专项能力
- `observability` 负责横切可观测性基础设施
- `schemas` 负责共享数据契约

### 全局规则

1. 上层可以依赖下层或共享层，但必须符合架构定义。
2. 下层不得反向依赖 API 层或编排层。
3. `observability` 可被 API / services / providers 等层依赖，但不得反向依赖业务编排实现。
4. `schemas` 应保持稳定，避免被临时需求污染。
5. 严禁产生循环依赖。
6. 跨层调用必须有明确理由，不能随意穿透。

---

## 6. 根目录文档职责矩阵

为避免根目录四文档重复与漂移，执行时以如下矩阵为准：

1. `AGENTS.md`
   - 定义长期协作规则、分层边界、文档治理、变更控制与模块-skill 映射
2. `PROJECT_PLAN.md`
   - 定义阶段目标、当前范围、优先级与路线图，不承载模块内部设计
3. `ARCHITECTURE.md`
   - 定义系统分层、依赖方向、调用关系与结构演进约束
4. `CODE_REVIEW.md`
   - 定义审查标准、风险点、验收方式与拒绝条件

---

## 7. 新增目录或能力的规则

未来向 `app/` 下新增目录时，必须满足：

1. 与现有层职责有明显差异
2. 职责可以用一小段清楚解释
3. 依赖方向明确
4. 不与已有模块职责重复
5. 新目录建立后，必须补充对应模块文档

例如未来可能新增：

- `app/rag/`
- `app/agents/`
- `app/tooling/`
- `app/evaluation/`

但必须在进入对应阶段后再新增，不能提前空建。

---

## 8. 与 Codex / AI Coding Agent 协作规则

当使用 Codex 或其他 AI Coding Agent 协助开发时，必须遵守：

1. 先阅读根目录四个总文档
2. 再阅读目标模块自己的 `AGENTS.md`
3. 再阅读对应 skill 与 checklist / test matrix / boundary 文档
4. 不允许只根据文件名臆断架构
5. 修改代码前必须先判断代码应落在哪一层
6. 进行较大改动前，应先说明是否影响模块边界与阶段边界

---

## 9. 全局开发原则

整个仓库范围内，代码应尽量满足：

- 显式优于隐式
- 稳定优于花哨
- 清晰优于过度抽象
- 分层优于混写
- 可测试优于难验证
- 可替换优于强绑定
- 可审查优于“看不懂但能跑”

---

## 10. 全局测试原则

项目整体应持续保障以下核心能力的回归安全：

- 配置加载正确性
- API 到 service 主链路正确性
- Prompt 查找与渲染行为
- Provider 归一化行为
- Context 基础行为与短期记忆行为
- Observability 基础行为
- 核心数据契约稳定性

测试体系可逐步演进，但核心路径必须始终可验证。

---

## 11. 文档维护原则

1. 根目录文档只在项目级规则变化时更新。
2. 模块内部细节变化时，应优先更新模块自身 `AGENTS.md`。
3. 不允许把模块补丁式细节长期堆到根目录文档中。
4. 文档事实必须跟随代码现实，不能让文档长期落后于实现。

---

## 12. 当前阶段项目总体目标

当前阶段，本项目的总体目标不是做全能力 AI 平台，而是先把以下能力做稳：

- 基础 API 接入能力
- 基础 LLM 调用主链路
- Prompt 资产能力
- Context 能力
- 多 Provider 接入能力
- Observability 治理能力
- Schema 契约能力
- 文档治理与测试能力

### 当前阶段能力声明（强约束）

当前阶段已经完成并要求稳定：

- 统一 HTTP 服务入口（`app/server.py`）
- `/chat` 单轮非流式主路径
- `/chat/reset` 会话重置入口
- API -> services -> context/prompts/providers -> schemas 基础调用链
- Phase 2 的 token-aware context 主链路
- 主链路最小测试门禁
- observability 最小基础设施与文档治理闭环

当前阶段已完成的 Context Engineering Phase 2 现实：

1. 默认主链路已切换为：
   `token-aware selection -> token-aware truncation -> deterministic summary -> serialization`
2. `request_assembler.py` 已成为正式上下文装配入口
3. `ContextManager` / `BaseContextStore` / `InMemoryContextStore` 已形成清晰 façade 与 store contract
4. `/chat/reset`、`reset_session`、`reset_conversation` 已打通
5. 已具备可持久化短期记忆能力，并保持不进入长期记忆/RAG

### 当前阶段现实：Context Engineering Phase 3（已落地）

当前仓库已在 Phase 2 主链路基础上落地 **Phase 3：持久化短期记忆（Persistent Session Memory）**，关键事实如下：

1. **可配置 store backend**  
   已支持 `CONTEXT_STORE_BACKEND=memory|redis`，并通过 `ContextStorageConfig` 管理持久化配置。

2. **Redis 持久化 store 已落地**  
   `app/context/stores/redis_store.py` 已实现 `get/append/replace/reset` 等 store contract，保留 `InMemoryContextStore` 作为 dev/test fallback。

3. **会话生命周期治理已接入**  
   已支持 `CONTEXT_SESSION_TTL_SECONDS`、`CONTEXT_STORE_KEY_PREFIX`、`reset_session`、`reset_conversation` 语义，且 reset 行为通过 `ContextManager` 统一暴露。

4. **持久化读写路径已稳定化**  
   request-time 与 response-time 均通过 `ContextManager` + store contract 访问上下文；API/service 不直接操作 Redis。

5. **测试与文档已追平**  
   已补齐 Redis store、backend parity、TTL、assembler integration、API/service 回归测试，并同步回写文档。

### 当前明确范围外（仍不做）

- streaming 真实链路
- 多模态真实链路
- tools/function calling 真正执行链路
- 结构化输出真实能力
- 向量数据库 / 语义检索 / RAG
- 用户长期画像记忆
- 长期记忆平台
- 多区域分布式状态协调
- 新 provider 的完整扩张

---

## 13. 一句话总结

本仓库采用“项目总纲 + 模块细则 + skill 执行约束”的治理方式。  
当前项目已完成 Phase 2 主链路，并进入 **Phase 3：持久化短期记忆**。本阶段的目标是把短期会话能力从“单实例内存骨架”升级为“产品可用的持久化 session memory”，但不提前进入 RAG 或长期记忆平台。

---

## 14. 文档驱动执行链路（强制）

所有开发任务必须按以下顺序执行，不得跳步：

1. 根目录文档：`AGENTS.md -> PROJECT_PLAN.md -> ARCHITECTURE.md -> CODE_REVIEW.md`
2. 目标模块 `AGENTS.md`
3. 对应 skill 与 checklist / test matrix / boundary 文档
4. 代码实现
5. 自审与 code review
6. 文档回写

标准闭环为：

`根目录文档 -> 模块 AGENTS -> 对应 skill -> 代码实现 -> review -> 文档回写`

---

## 15. 模块到 Skill 映射（强制）

- API 类任务：`app/api/AGENTS.md` -> `skills/python-api-capability/`
- Context 类任务：`app/context/AGENTS.md` -> `skills/python-context-capability/`
- Prompt 类任务：`app/prompts/AGENTS.md` -> `skills/python-prompt-capability/`
- Provider 通用任务：`app/providers/AGENTS.md` -> `skills/python-ai-provider-capability/`
- LLM Provider 任务：`app/providers/AGENTS.md` -> `skills/python-llm-provider-capability/`
- Services 类任务：`app/services/AGENTS.md`，并按任务内容匹配 API / Context / Prompt / Provider skill
- Schemas 类任务：`app/schemas/AGENTS.md`
- Observability 类任务：`app/observability/AGENTS.md` -> `skills/python-observability-capability/`
- Tests 类任务：`tests/AGENTS.md`，并按被测模块匹配对应 skill

---

## 16. 文档更新触发规则（强制）

### 必须更新根目录文档的场景

- 项目分层变化
- 全局依赖方向变化
- 项目阶段目标变化
- 全局审查门禁变化
- 新增 `app/` 一级能力目录

### 必须更新模块 `AGENTS.md` 的场景

- 模块职责变化
- 模块内边界变化
- 模块调用入口/出口变化
- 模块内 review 重点变化

### 必须更新 skill 文档的场景

- 任务执行步骤变化
- checklist / test matrix 变化
- 模块映射关系变化
- 产出物和验收标准变化

### 新增能力的先后顺序

1. 先更新根目录文档（若影响全局）
2. 再更新目标模块 `AGENTS.md`
3. 再更新对应 skill 与 checklist / test matrix
4. 最后进行代码实现与测试
5. 合并前完成文档回写一致性检查
