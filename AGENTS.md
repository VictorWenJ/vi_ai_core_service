# AGENTS.md

> 更新日期：2026-04-07


## 1. 文档定位

本文件用于定义 `vi_ai_core_service` 仓库级别的协作规则、工程边界、开发原则与文档治理方式。

它是本项目的**顶层协作文档**。

本文件不替代模块级文档。  
当开发者、协作成员或 Codex 需要修改某个具体模块时，必须按以下顺序阅读文档：

1. 根目录 `AGENTS.md`
2. 根目录 `PROJECT_PLAN.md`
3. 根目录 `ARCHITECTURE.md`
4. 根目录 `CODE_REVIEW.md`
5. 目标模块目录下的 `AGENTS.md`

---

## 2. 项目定位

`vi_ai_core_service` 是 VI AI Project 中的 Python AI 子系统。

当前阶段，本仓库聚焦于以下能力：

- 大模型 API 接入
- Prompt 资产组织与渲染
- 上下文管理
- AI 请求编排
- 对外 API 暴露
- 可观测性基础设施治理
- AI 能力相关的数据契约管理

本仓库的目标不是做一个“大而全”的业务系统，  
而是作为整个项目中的 **Python 侧 AI 能力核心服务**。

---

## 3. 当前项目范围

当前版本的项目范围明确限定为以下七层：

1. API 接入层（`app/api/`）
2. 应用编排层（`app/services/`）
3. 上下文管理层（`app/context/`）
4. Prompt 资产层（`app/prompts/`）
5. 模型 API 接入层（`app/providers/`）
6. 可观测性基础设施层（`app/observability/`）
7. 数据模型层（`app/schemas/`）

其中 `app/observability/` 为横切基础设施模块，当前负责统一日志上报入口（`log_until.py`）与日志输出格式约束，不承担业务流程编排。

未来如果需要新增新层，例如 `app/rag/`、`app/agents/` 等，必须在项目级文档中明确纳入，并同步定义边界。

---

## 4. 项目级治理原则

### 4.1 文档分层治理

本仓库采用“文档分层治理”模式：

- 根目录文档只负责项目总体规则
- 模块目录文档只负责该模块自身规则
- 根目录文档不得越权写模块内部细节
- 模块文档不得随意突破项目总体原则

### 4.2 边界清晰优先

每个目录、每一层都必须有明确职责。  
不允许无边界地混合：

- 路由逻辑
- 编排逻辑
- Provider 适配逻辑
- Prompt 逻辑
- Context 逻辑
- Observability 基础设施逻辑
- Schema 契约逻辑

### 4.3 渐进式演进优先于过度设计

项目允许演进，但不接受没有实际需求支撑的提前抽象。  
当前阶段应优先保证：

- 结构清晰
- 调用链清晰
- 模块边界稳定
- 代码易于继续扩展

### 4.4 可替换、可维护、可扩展

本项目应尽量具备以下特征：

- 抽象合理
- 依赖方向清晰
- 底层实现可替换
- 上层调用稳定
- 模块之间低耦合

### 4.5 AI 工程能力是核心能力，不是附属能力

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
- `observability` 负责提供横切可观测性基础设施（统一日志上报与格式约束）
- `schemas` 负责提供共享数据契约

### 全局规则

1. 上层可以依赖下层或共享层，但必须符合架构定义
2. 下层不得反向依赖 API 层或编排层
3. `observability` 可被 API/services/providers 等层依赖，但不得反向依赖业务编排实现
4. `schemas` 应作为最稳定的共享契约层之一
5. 严禁产生循环依赖
6. 模块之间的跨层调用必须有明确理由，不能随意穿透

---

## 6. 根目录文档的职责边界

### 根目录文档应该定义什么

根目录文档应该定义：

- 项目目标
- 项目总体架构
- 项目阶段规划
- 全局工程规则
- 全局 Code Review 标准
- 全局文档治理方式
- 全局模块边界与依赖原则

### 根目录文档不应该定义什么

根目录文档不应该定义：

- 某个 provider 如何接入
- 某个 prompt 模板如何命名
- 某个 context store 如何实现
- 某个 service 内部如何拆分函数
- 某个 API 文件内部怎么组织路由
- 某个 schema 的字段设计细节

这些内容属于模块级文档职责。

---

## 6.1 根目录四文档职责矩阵（防漂移）

为避免根目录四文档重复与漂移，执行时以如下矩阵为准：

1. `AGENTS.md`
   - 定义长期协作规则、分层边界、文档治理、变更控制与模块-skill 映射
2. `PROJECT_PLAN.md`
   - 定义阶段目标、当前范围、优先级与路线图，不承载模块内部设计
3. `ARCHITECTURE.md`
   - 定义系统分层、依赖方向、调用关系与结构演进约束
4. `CODE_REVIEW.md`
   - 定义审查标准、风险点、验收方式与拒绝条件

出现冲突时的处理顺序：

- 先校正事实（代码/测试）与 `ARCHITECTURE.md` 的边界一致性
- 再按 `PROJECT_PLAN.md` 判断是否属于当前阶段
- 最后由 `AGENTS.md` 与 `CODE_REVIEW.md` 收敛执行与审查动作

---

## 7. 新增目录或新增能力的规则

未来向 `app/` 下新增新目录时，必须满足以下条件：

1. 新能力与现有层职责有明显差异
2. 新目录的职责可以用一小段清楚解释
3. 新目录的依赖方向是明确的
4. 新目录不会和已有模块职责重复
5. 新目录建立后，必须补充对应模块文档

例如未来可能新增：

- `app/rag/`
- `app/agents/`
- `app/tooling/`
- `app/evaluation/`

但必须在项目进入相应阶段后再新增，不能提前空建。

### 基础设施模块新增规则（新增）

若新增的是横切基础设施模块（如 observability），必须额外满足：

1. 明确技术选型（当前 observability 统一使用 Python 标准库 `logging`）
2. 明确日志格式（当前统一为“控制台前缀 + `message=<json>`”）
3. 明确日志内容策略（当前阶段业务 payload 默认可输出；凭据字段如 API key/Authorization 必须禁止输出）
4. 明确模块边界（不承担业务编排、不替代 API/service/provider）
5. 明确当前阶段只落最小基础设施，不做 tracing/metrics/alerting 平台化建设

---

## 8. 与 Codex / AI Coding Agent 协作规则

当使用 Codex 或其他 AI Coding Agent 协助开发时，必须遵守：

1. 先阅读根目录四个总文档
2. 再阅读目标模块自己的 `AGENTS.md`
3. 不允许只根据文件名臆断架构
4. 不允许把项目级规则和模块级规则混写
5. 修改代码前应先判断代码应落在哪一层
6. 进行较大改动前，应先说明是否影响模块边界

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
- Context 基础行为
- Observability 基础行为（结构化输出与错误日志语义）
- 核心数据契约稳定性

测试体系可以逐步演进，但核心路径必须始终可验证。

---

## 11. 文档维护原则

1. 根目录文档只在项目级规则发生变化时更新
2. 模块内部细节变化时，应优先更新模块自己的 `AGENTS.md`
3. 不允许把模块细节补丁式堆到根目录文档中
4. 当某模块复杂度上升时，可将其局部 `AGENTS.md` 拆分为：
   - `AGENTS.md`
   - `PROJECT_PLAN.md`
   - `ARCHITECTURE.md`
   - `CODE_REVIEW.md`

---

## 12. 当前阶段项目总体目标

当前阶段，本项目的总体目标不是做全能力 AI 平台，而是先把以下能力做稳定：

- 基础 API 接入能力
- 基础 LLM 调用主链路
- 基础 Prompt 资产能力
- 基础 Context 能力
- 多 Provider 接入能力
- 基础 observability 代码与治理能力
- 基础 Schema 契约能力
- 基础测试与文档治理能力

### 当前阶段能力声明（强约束）

当前阶段只验收“基础设施 + 单轮非流式主链路”，明确为：

- 当前已实现并要求稳定：
  - 统一 HTTP 服务入口（`app/server.py`），仅支持通过 HTTP 调用
  - `/chat` 单轮会话主路径
  - 非流式输出（`stream=False`）
  - API -> services -> context/prompts/providers -> schemas 基础调用链
  - 覆盖主链路的最小测试门禁
  - observability 最小基础设施实现（`log_until.py` 统一日志入口 + 前缀/JSON 输出约束）与文档治理闭环
- 当前仅预留，不作为本阶段已实现能力：
  - streaming
  - 多模态真实链路
  - tools/function calling 真正执行链路
  - structured output 真正能力
  - context persistence/summary/compaction
  - 新 provider 的完整落地

#### 当前阶段能力增强（Context Engineering Phase 2）

随着项目进入 Context Engineering Phase 2，本阶段在前述基础能力之上增加以下能力并明确约束：

1. **Token‑aware 上下文策略**：context 层引入 `TokenAwareWindowSelectionPolicy` 与 `TokenAwareTruncationPolicy`，根据会话历史的 token 数量动态选择并截断历史，避免全量拼接；默认以可配置的最大 token 预算为界，替换 Phase 1 的“最近 N 条”策略。
2. **Summary/Compaction 策略**：定义 `SummaryPolicy` 接口，并提供默认简单实现（例如截断提示或取每条消息首句），用于在超过 token 预算时压缩历史。该策略仅提供 hook，不调用外部 LLM；真实摘要将在后续阶段实现。
3. **会话重置能力**：`ContextManager` 增加 `reset_conversation` 等方法；服务层与 API 层提供会话重置接口，允许用户主动清除当前 session/conversation 历史。重置操作仅影响短期会话，不能跨用户或跨会话误删数据。
4. **ContextPolicyPipeline 升级**：升级默认的 context policy pipeline，执行顺序为 token‑aware 选择 → token‑aware 截断 → summary/compaction → serialization，并将执行 trace 写入 metadata。`request_assembler.py` 必须通过该管道获取历史。
5. **配置与默认值更新**：在配置中新增最大 token 预算、截断预算、summary 开关等参数，确保可以灵活调整策略行为；`defaults.py` 应提供实例化这些策略的工厂函数。

这些增强能力仍仅针对短期会话窗口控制和重置；不代表我们已经实现了复杂的 long‑term memory 平台、RAG 记忆耦合或多模态链路。任何持久化存储、检索、流式输出等高级能力仍属于未来阶段，不能在当前阶段提前实现或穿透边界。

---

## 13. 一句话总结

本仓库采用“项目总纲 + 模块细则”的治理方式。  
根目录文档负责**全局原则、总体规划、总体架构与总体审查标准**；  
各模块目录文档负责**该模块的详细规则与实现边界**。

---

## 14. 文档驱动执行链路（强制）

本项目后续所有开发任务，必须按以下顺序执行，不得跳步：

1. 先读根目录文档（`AGENTS.md` -> `PROJECT_PLAN.md` -> `ARCHITECTURE.md` -> `CODE_REVIEW.md`）
2. 定位归属模块并阅读该模块 `AGENTS.md`
3. 匹配并执行对应 skill（`SKILL.md` + checklist/test matrix + boundary/acceptance 文档）
4. 实施代码改动（仅在模块边界内）
5. 按根目录 `CODE_REVIEW.md` + 模块 `AGENTS.md` + skill checklist 进行自审
6. 若代码事实变化影响文档描述，执行文档回写（根文档/模块文档/skill 文档）

标准闭环为：

`根目录文档 -> 模块 AGENTS -> 对应 skill -> 代码实现 -> review -> 文档回写`

---

## 15. 模块到 Skill 映射（强制）

模块任务必须映射到对应 skill，不允许“无 skill 自由发挥”：

- API 类任务：根目录四文档 -> `app/api/AGENTS.md` -> `skills/python-api-capability/`
- Context 类任务：根目录四文档 -> `app/context/AGENTS.md` -> `skills/python-context-capability/`
- Prompt 类任务：根目录四文档 -> `app/prompts/AGENTS.md` -> `skills/python-prompt-capability/`
- Provider 通用任务：根目录四文档 -> `app/providers/AGENTS.md` -> `skills/python-ai-provider-capability/`
- LLM Provider 任务：根目录四文档 -> `app/providers/AGENTS.md` -> `skills/python-llm-provider-capability/`
- Services 类任务：根目录四文档 -> `app/services/AGENTS.md`，并按任务内容匹配 API/Context/Prompt/Provider 对应 skill
- Schemas 类任务：根目录四文档 -> `app/schemas/AGENTS.md`，并按契约关联能力选择对应 skill
- Observability 类任务：根目录四文文档 -> `app/observability/AGENTS.md` -> `skills/python-observability-capability/`
- Tests 类任务：根目录四文文档 -> `tests/AGENTS.md`，并按被测模块匹配对应 skill

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
- checklist/test matrix 变化
- 模块映射关系变化
- 产出物和验收标准变化

### 新增能力的先后顺序

1. 先更新根目录文档（若影响全局）
2. 再更新目标模块 `AGENTS.md`
3. 再更新对应 skill 与 checklist/test matrix
4. 最后进行代码实现与测试
5. 合并前完成文档回写一致性检查
