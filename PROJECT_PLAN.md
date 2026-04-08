# PROJECT_PLAN.md

> 更新日期：2026-04-08

## 1. 文档定位

本文件定义 `vi_ai_core_service` 的项目级阶段规划与演进路线。  
本文件只描述项目整体层面的建设目标、阶段重点、优先级与里程碑，不展开到具体模块内部实现细节。

---

## 2. 项目总体目标

`vi_ai_core_service` 的总体目标是：

构建一个边界清晰、结构可扩展、具备多模型接入能力的 Python AI 核心服务，为后续更完整的 AI 应用能力建设提供稳定基础。

当前项目不追求能力数量，而是先建立：

- 正确的目录结构
- 正确的分层方式
- 正确的文档体系
- 正确的调用链
- 正确的能力边界

---

## 3. 当前阶段建设原则

### 3.1 先打基础，再扩能力

当前优先级是：

1. 项目级文档治理
2. 模块级文档治理
3. 基础调用链稳定
4. 基础 Provider 能力稳定
5. 基础 Prompt / Context 能力稳定
6. 测试与回归保护

### 3.2 先做主链路，再做高级特性

当前优先保障：

- 请求能够正确进入系统
- 能正确完成 Prompt / Context / Provider 协作
- 能得到一致、可测试的返回结果

高级特性如：

- RAG
- Agent
- Tool orchestration
- 多模态
- Streaming 深度治理

可以后续逐步引入。

### 3.3 先保证边界正确，再考虑复杂度提升

如果边界不清晰，即使功能跑通，也会让后续演进成本快速上升。  
所以当前阶段，架构边界和文档治理优先级很高。

### 3.4 当前阶段能力声明（强约束）

当前阶段已实现并要求稳定：

- HTTP 服务化调用方式（`app/server.py`）为唯一运行入口
- LLM API 单轮会话
- 非流式输出（`stream=False`）
- API -> services -> prompts/context/providers 主链路
- observability 最小基础设施实现
- Phase 2 的 token-aware context 主链路与 reset 能力

当前仅预留，不作为本阶段验收项：

- streaming 真实链路
- 多模态真实落地
- tools/function calling 真实实现
- structured output 真实实现
- RAG / 语义检索
- 长期记忆平台
- 新 provider 的完整接入

---

## 4. 当前已确认的系统层次

当前项目按以下七层组织：

1. API 接入层
2. 应用编排层
3. 上下文管理层
4. Prompt 资产层
5. 模型 API 接入层
6. 可观测性基础设施层
7. 数据模型层

---

## 5. 项目阶段划分

## 阶段一：文档治理与结构固化

### 目标

建立项目级与模块级文档体系，明确项目边界、模块边界、依赖方向与开发规则。

### 完成标准

- 项目总纲清晰
- 模块职责清晰
- 文档边界清晰
- Codex 协作入口清晰

---

## 阶段二：基础主链路稳定化

### 目标

让系统当前已有的基础主链路结构稳定，做到可运行、可理解、可测试。

### 完成标准

- API -> services -> prompts/context/providers 主链路稳定
- 基础 LLM 调用流程稳定
- 基础测试可支撑回归

---

## 阶段三：Provider 体系增强

### 目标

让模型接入层从“能接多个厂商”进一步演进到“接入规则统一、维护成本可控”。

### 完成标准

- provider 抽象统一
- registry 稳定
- 新增 provider 有清晰接入规范
- 上层不承受大量厂商特例

---

## 阶段四：Prompt 与 Context 能力增强

### 目标

让 Prompt 与 Context 从“基础可用”进入“可治理、可扩展”状态。

### 完成标准

- Prompt 资产不再零散
- Context 结构不再混乱
- 后续扩展不会推翻现有基础

### 阶段四-A：Context Engineering Phase 1

#### 目标

把服务端历史如何进入一次模型请求做成正式上下文治理流程。

#### 完成标准

- `request_assembler.py` 升级为正式上下文装配入口
- history selection / truncation / serialization 具备清晰接口
- 最近 N 条消息窗口治理具备可测试默认实现

### 阶段四-B：Context Engineering Phase 2

#### 目标

将 Context skeleton 升级为 token-aware，具备预算感知的窗口选择、截断和摘要/压缩能力，并提供会话重置能力。

#### 当前状态（2026-04-08）

主链路已落地并进入维护阶段。默认策略已为：

`token-aware selection -> token-aware truncation -> deterministic summary -> serialization`

并已接入 reset 接口与 metadata trace。

#### 完成标准

1. `TokenAwareWindowSelectionPolicy` 落地并成为默认 selection
2. `TokenAwareTruncationPolicy` 落地并成为默认 truncation
3. `SummaryPolicy` 落地并接入默认 pipeline
4. `/chat/reset`、`reset_session`、`reset_conversation` 打通
5. trace / metadata / 测试 / 文档 已与代码现实对齐

### 阶段四-C：Context Engineering Phase 3（持久化短期记忆）

#### 目标

在 Phase 2 主链路基础上，为 session / conversation history 引入**持久化短期记忆能力**，让短期记忆从“单实例内存骨架”升级为“产品可用的持久化会话状态”。

#### 重点

1. **持久化 store 引入**  
   推荐新增 `RedisContextStore` 作为主实现，保留 `InMemoryContextStore` 作为 dev/test fallback。

2. **配置拆分与治理**  
   新增 `ContextStorageConfig`（或等价命名）用于管理：
   - store backend
   - redis url
   - key prefix / namespace
   - session TTL
   - conversation 级 reset 语义
   并与 `ContextPolicyConfig` 保持职责分离。

3. **持久化读写主链路**  
   - request-time 读取持久化 session history
   - response-time 通过 manager/store 统一追加 user / assistant 消息
   - 保证 API / service 不直接操作 Redis 或持久化细节

4. **会话生命周期治理**  
   明确 session TTL、conversation reset、session reset、replace 语义，以及 dev/test fallback 行为。

5. **测试与文档同步升级**  
   覆盖配置、store contract、reset 语义、读写路径、fallback 行为与回归测试。

#### 范围内

- store contract 升级
- `RedisContextStore`（或等价持久化短期记忆实现）
- `ContextManager` 持久化 façade 行为
- `chat_service.py` / `request_assembler.py` 的持久化读写接入
- reset / TTL / namespace 行为
- 文档治理与测试同步更新

#### 范围外

- 向量数据库
- 语义检索
- 长期记忆平台
- 外部 LLM 驱动的高级摘要系统
- RAG / retrieval
- 用户画像与跨会话语义记忆
- 多区域分布式状态编排

#### 本阶段完成标准

1. store backend 可配置，默认支持 `memory` 与 `redis`
2. request-time 能从持久化 store 读取 session history
3. response-time 能稳定写回 user / assistant 历史
4. `reset_session` / `reset_conversation` 在持久化 store 上行为正确
5. TTL / key prefix / namespace 语义清晰、可测试
6. 文档、skill、测试与代码事实一致

#### 当前状态（2026-04-08）

Phase 3 主链路已落地并通过回归测试，当前事实为：

- 已新增 `RedisContextStore`，并保留 `InMemoryContextStore`
- 已引入 `ContextStorageConfig`，支持：
  - `CONTEXT_STORE_BACKEND`
  - `CONTEXT_REDIS_URL`
  - `CONTEXT_SESSION_TTL_SECONDS`
  - `CONTEXT_STORE_KEY_PREFIX`
  - `CONTEXT_ALLOW_MEMORY_FALLBACK`
- `ContextManager` 已接入 backend 选择并保持 façade 契约
- `/chat` 与 `/chat/reset` 在 Redis backend 下可运行
- TTL、reset、backend parity、assembler integration 测试已覆盖

### 阶段四-D：Context Engineering Phase 4（结构化短期记忆与检索前置）

#### 目标

在持久化短期记忆稳定后，引入更接近产品效果的结构化短期记忆与检索前置能力，为未来 `app/rag/` 与长期记忆做准备。

#### 可能方向

- rolling summary
- structured session memory
- task / goal state
- memory extraction hooks
- retrieval-ready context lane

#### 明确不等于

- 直接进入长期记忆平台
- 直接进入 RAG 主链路
- 直接引入向量检索系统

---

## 阶段五：系统扩展准备

### 目标

在现有七层稳定后，为未来新增能力模块做准备。

### 可能方向

- `app/rag/`
- `app/agents/`
- `app/tooling/`
- `app/evaluation/`
- integration tests / e2e tests

### 注意

这些方向不是当前阶段必须立即实现的内容，只有在基础足够稳定后，才进入正式项目计划。

---

## 6. 当前阶段优先级排序

### P0：必须优先完成

- 根目录文档体系正确建立
- 模块级文档体系正确建立
- 七层边界清晰
- 主链路清晰
- 基础测试可用
- Phase 2 主链路与 reset 能力稳定
- Phase 3 持久化短期记忆能力稳定（backend/TTL/reset/回归）

### P1：当前阶段重要但可稍后推进

- context trace 与 token accounting 收紧
- 结构化短期记忆雏形
- request assembly 与持久化读写链路一致性

### P2：后续阶段能力

- RAG
- Agent
- Tool use
- 多模态
- 长期记忆
- 更复杂的检索与调度

---

## 7. 当前阶段不建议做的事情

1. 提前新增大量未来目录
2. 过早把系统拆成过多抽象层
3. 为没有需求的能力设计复杂框架
4. 在没有文档约束前大规模重构
5. 在模块边界不清晰时继续快速叠功能
6. 把 Phase 3 直接做成长期记忆或 RAG 工程

---

## 8. 项目推进方式

项目建议按以下方式推进：

1. 先固化文档体系
2. 再校正目录与分层
3. 再稳定主链路
4. 再增强 provider / prompt / context
5. 最后再考虑新增系统能力

在 Phase 3 中继续沿用这一节奏：

1. 先升级根目录文档
2. 再升级 `app/context/AGENTS.md`、`app/services/AGENTS.md`、`app/api/AGENTS.md`、`tests/AGENTS.md`
3. 再升级 `skills/python-context-capability/` 及其资产文档
4. 再落地 Redis/store/config/manager/service/API 代码
5. 最后补测试与文档回写

---

## 9. 里程碑定义

### M1：文档治理完成
- 根目录四文档完成
- 关键模块 `AGENTS.md` 完成
- 文档边界清晰

### M2：主链路稳定
- API -> service -> provider/prompt/context 链路稳定
- 基础测试可用

### M3：Provider 体系规范化
- 新增 provider 有明确规范
- 归一化行为稳定

### M4-A：Context Engineering Phase 1 完成
- `request_assembler.py` 成为正式上下文装配入口
- selection / truncation / serialization 接口化

### M4-B：Context Engineering Phase 2 完成
- token-aware selection/truncation/summary/reset 全部接通
- 默认主链路切换完成
- 测试与 trace 可回归

### M4-C：Context Engineering Phase 3 完成
- Redis（或等价持久化 store）接入
- 持久化读写路径稳定
- TTL / namespace / reset 语义正确
- 文档、skill、测试完成追平

### M4-D：Context Engineering Phase 4 完成
- 结构化短期记忆与 rolling summary 能力形成雏形
- 为 `app/rag/` / 长期记忆预留清晰边界

### M5：扩展能力准备完成
- 可以有序引入 RAG / Agent 等新模块，而不破坏现有体系

---

## 10. 一句话总结

本项目当前的核心计划不是“快速堆功能”，而是先完成**文档治理、结构治理、主链路稳定化和 AI 能力基础设施固化**。  
Phase 2 已让请求时上下文治理成型；Phase 3 将把短期会话能力升级为持久化 session memory；Phase 4 再进入更接近产品效果的结构化短期记忆与检索前置能力。

---

## 11. 文档驱动闭环计划

从当前轮次开始，项目执行模式固定为：

`根目录文档 -> 模块 AGENTS -> 对应 skill -> 代码实现 -> review -> 文档回写`

### 阶段化落地要求

- 阶段 1：审查根文档、模块文档、skills 和核心代码现实，输出不一致点
- 阶段 2：先修文档治理体系，再进入代码升级
- 阶段 3：基于新文档体系输出 `P0/P1/P2` 升级清单
- 阶段 4：按优先级做小步代码改造与必要测试
- 阶段 5：交付文档升级、代码升级、验证结果与标准流程模板

### 里程碑门禁

- 没有完成文档链路定义，不进入代码改动
- 没有完成模块-skill 映射，不进入大于单文件的重构
- 没有完成回写检查，不允许视为任务完成

### Phase 3 专项门禁

- 未定义持久化 store contract 与配置边界，不进入持久化实现
- 未明确 `ContextStorageConfig`（或等价配置）与 `ContextPolicyConfig` 的职责分离，不进入配置改造
- 未明确 session / conversation TTL 与 reset 语义，不进入 Redis store 开发
- 未更新文档与 skill，不上线持久化短期记忆能力
