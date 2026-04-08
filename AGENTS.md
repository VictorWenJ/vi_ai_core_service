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
6. 对应 skill 文档与 checklist / test matrix / boundary 文档（若存在）

---

## 2. 项目定位

`vi_ai_core_service` 是 VI AI Project 中的 Python AI 子系统。

当前阶段，本仓库聚焦于以下能力：

- 大模型 API 接入
- Prompt 资产组织与渲染
- 上下文管理与短期记忆治理
- 持久化短期记忆
- AI 请求编排
- 对外 API 暴露
- 可观测性基础设施治理
- AI 能力相关的数据契约管理
- 本地运行时与部署基础设施治理（`infra/`）

本仓库不是“大而全”的业务系统，而是整个项目中的 Python 侧 AI 核心服务。

---

## 3. 当前项目范围

当前版本仍限定为以下七层业务/系统分层：

1. API 接入层（`app/api/`）
2. 应用编排层（`app/services/`）
3. 上下文管理层（`app/context/`）
4. Prompt 资产层（`app/prompts/`）
5. 模型 API 接入层（`app/providers/`）
6. 可观测性基础设施层（`app/observability/`）
7. 数据模型层（`app/schemas/`）

其中 `app/observability/` 为横切基础设施模块，当前负责统一日志上报入口与日志输出格式约束，不承担业务流程编排。

### 3.1 关于 `infra/` 的定位

新增的 `infra/` **不是第八层业务/系统分层**。  
它属于项目级的**工程基础设施 / 运行时交付能力目录**，用于治理：

- Dockerfile
- compose/容器编排
- 本地运行时依赖（如 Redis）
- 环境变量样例
- 开发/联调/交付方式说明

`infra/` 的存在不会改变当前七层业务架构，只是为代码提供更稳定的运行与部署方式。

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
- 运行时基础设施逻辑（Docker / compose / Redis 编排）

### 4.3 渐进式演进优先于过度设计

项目允许演进，但不接受没有实际需求支撑的提前抽象。  
当前阶段优先保证：

- 结构清晰
- 调用链清晰
- 模块边界稳定
- 代码与文档一致
- 可测试、可回归
- 本地运行环境可复现

### 4.4 可替换、可维护、可扩展

本项目应尽量具备以下特征：

- 抽象合理
- 依赖方向清晰
- 底层实现可替换
- 上层调用稳定
- 模块之间低耦合
- 运行时基础设施可替换且不绑死开发机环境

---

## 5. 全局依赖方向

本仓库整体上应遵守如下业务依赖方向：

`api -> services -> context/prompts/providers -> schemas`

更准确地说：

- `api` 负责接收请求并转发
- `services` 负责用例级编排
- `context/prompts/providers` 负责提供专项能力
- `observability` 负责横切可观测性基础设施
- `schemas` 负责共享数据契约

### 5.1 工程基础设施的依赖约束

- `infra/` 不属于业务依赖链的一环
- `app/` 代码不得在运行时反向依赖 `infra/` 中的脚本或 compose 文件
- `infra/` 负责“如何运行系统”，不负责“如何实现业务”
- Redis 作为外部依赖由 `app/context/stores/*` 通过配置访问，而不是通过 `infra/` 代码耦合访问

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

未来新增目录时，必须满足：

1. 职责可以清楚解释
2. 不与已有模块职责重复
3. 依赖方向明确
4. 建立后必须补充对应模块文档

### 7.1 `infra/` 目录的新增原则

`infra/` 作为项目级工程基础设施目录，可以包含：

- Dockerfile
- compose 文件
- 根目录 `.env.example`（项目级模板，唯一标准来源）
- 可选 `infra/.env.compose.example`（仅 compose 专属变量）
- 本地依赖服务编排
- 基础运行说明

但不应包含：

- 业务逻辑
- Provider 代码
- Prompt 模板
- Context policy 实现
- Service 编排实现

---

## 8. 与 Codex / AI Coding Agent 协作规则

当使用 Codex 或其他 AI Coding Agent 协助开发时，必须遵守：

1. 先阅读根目录四个总文档
2. 再阅读目标模块自己的 `AGENTS.md`
3. 再阅读对应 skill 与 checklist / test matrix / boundary 文档（若存在）
4. 不允许只根据文件名臆断架构
5. 修改代码前必须先判断代码应落在哪一层或哪个治理域
6. 进行较大改动前，应先说明是否影响模块边界、阶段边界与运行方式边界

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
- 本地环境可复现优于“只在作者电脑可跑”

---

## 10. 全局测试原则

项目整体应持续保障以下核心能力的回归安全：

- 配置加载正确性
- API 到 service 主链路正确性
- Prompt 查找与渲染行为
- Provider 归一化行为
- Context 基础行为与短期记忆行为
- Redis 持久化短期记忆行为
- Observability 基础行为
- 核心数据契约稳定性
- Docker/compose 本地联调方式可运行

---

## 11. 当前阶段能力声明（强约束）

当前阶段已实现并要求稳定：

- HTTP 服务化调用方式（`app/server.py`）为唯一运行入口
- LLM API 单轮会话
- 非流式输出（`stream=False`）
- API -> services -> prompts/context/providers 主链路
- Phase 2 的 token-aware context 主链路与 reset 能力
- Phase 3 的持久化短期记忆（Redis backend / fallback / TTL / reset）
- 工程级 `infra/` 目录，用于 app + redis 的 Docker 化本地运行与联调

当前明确范围外（仍不做）：

- streaming 真实链路
- 多模态真实链路
- tools/function calling 真正执行链路
- 结构化输出真实能力
- 向量数据库 / 语义检索 / RAG
- 用户长期画像记忆
- 长期记忆平台
- 多区域分布式状态协调

---

## 12. 一句话总结

本仓库采用“项目总纲 + 模块细则 + skill 执行约束 + 工程基础设施治理”的方式。  
当前项目已完成 Phase 2 主链路，并进入 **Phase 3：持久化短期记忆**。同时，`infra/` 被正式纳入治理，用于统一 Docker 与本地依赖服务管理，但它不是业务系统分层的一部分。

---

## 13. 文档驱动执行链路（强制）

所有开发任务必须按以下顺序执行，不得跳步：

1. 根目录文档：`AGENTS.md -> PROJECT_PLAN.md -> ARCHITECTURE.md -> CODE_REVIEW.md`
2. 目标模块 `AGENTS.md`
3. 对应 skill 与 checklist / test matrix / boundary 文档（若存在）
4. 代码实现
5. 自审与 code review
6. 文档回写

标准闭环为：

`根目录文档 -> 模块 AGENTS -> 对应 skill -> 代码实现 -> review -> 文档回写`

---

## 14. 模块到 Skill 映射（强制）

- API 类任务：`app/api/AGENTS.md` -> `skills/python-api-capability/`
- Context 类任务：`app/context/AGENTS.md` -> `skills/python-context-capability/`
- Prompt 类任务：`app/prompts/AGENTS.md` -> `skills/python-prompt-capability/`
- Provider 通用任务：`app/providers/AGENTS.md` -> `skills/python-ai-provider-capability/`
- LLM Provider 任务：`app/providers/AGENTS.md` -> `skills/python-llm-provider-capability/`
- Services 类任务：`app/services/AGENTS.md`，并按任务内容匹配 API / Context / Prompt / Provider skill
- Schemas 类任务：`app/schemas/AGENTS.md`
- Observability 类任务：`app/observability/AGENTS.md` -> `skills/python-observability-capability/`
- Tests 类任务：`tests/AGENTS.md`，并按被测模块匹配对应 skill
- Infra / Docker / compose 类任务：当前由 `infra/AGENTS.md` + 根目录四文档治理；**当前暂不单独建立 skill**

---

## 15. 文档更新触发规则（强制）

### 必须更新根目录文档的场景

- 项目分层变化
- 全局依赖方向变化
- 项目阶段目标变化
- 全局审查门禁变化
- 新增 `app/` 一级能力目录
- 新增项目级工程基础设施治理域（如 `infra/`）

### 必须更新模块 `AGENTS.md` 的场景

- 模块职责变化
- 模块内边界变化
- 模块调用入口/出口变化
- 模块内 review 重点变化
- 工程基础设施目录职责变化

### 新增能力的先后顺序

1. 先更新根目录文档（若影响全局）
2. 再更新目标模块 `AGENTS.md`
3. 再更新对应 skill 与 checklist / test matrix（若存在）
4. 最后进行代码实现与测试
5. 合并前完成文档回写一致性检查
