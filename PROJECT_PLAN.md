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
- 可复现的本地运行与交付方式

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
7. 本地运行基础设施标准化

### 3.2 先做主链路，再做高级特性

当前优先保障：

- 请求能够正确进入系统
- 能正确完成 Prompt / Context / Provider 协作
- 能得到一致、可测试的返回结果
- app + redis 本地联调方式稳定可复现

高级特性如：

- RAG
- Agent
- Tool orchestration
- 多模态
- Streaming 深度治理

可以后续逐步引入。

### 3.3 先保证边界正确，再考虑复杂度提升

如果边界不清晰，即使功能跑通，也会让后续演进成本快速上升。  
所以当前阶段，架构边界、文档治理和运行方式治理优先级都很高。

---

## 4. 当前阶段能力声明（强约束）

当前阶段已实现并要求稳定：

- HTTP 服务化调用方式（`app/server.py`）为唯一业务运行入口
- LLM API 单轮会话
- 非流式输出（`stream=False`）
- API -> services -> prompts/context/providers 主链路
- observability 最小基础设施实现
- Phase 2 的 token-aware context 主链路与 reset 能力
- Phase 3 的持久化短期记忆（Redis backend / fallback / TTL / reset）
- `infra/` 目录下的 Docker / compose 本地运行方式

当前仅预留，不作为本阶段验收项：

- streaming 真实链路
- 多模态真实落地
- tools/function calling 真实实现
- structured output 真实实现
- RAG / 语义检索
- 长期记忆平台
- 生产级高可用 Redis / 分布式一致性方案

---

## 5. 当前已确认的系统层次

当前项目按以下七层业务/系统分层组织：

1. API 接入层
2. 应用编排层
3. 上下文管理层
4. Prompt 资产层
5. 模型 API 接入层
6. 可观测性基础设施层
7. 数据模型层

同时存在一个**项目级工程基础设施治理域**：

- `infra/`

`infra/` 不属于第八层业务层，而是用于 Docker / compose / 本地依赖编排与交付方式治理。

---

## 6. 项目阶段划分

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
- `request_assembler.py` 成为正式上下文装配入口
- selection / truncation / serialization 接口化

### 阶段四-B：Context Engineering Phase 2
- token-aware selection/truncation/summary/reset 全部接通
- 默认主链路切换完成
- 测试与 trace 可回归

### 阶段四-C：Context Engineering Phase 3（持久化短期记忆）
- Redis（或等价持久化 store）接入
- 持久化读写路径稳定
- TTL / namespace / reset 语义正确
- 文档、skill、测试完成追平

### 阶段四-D：Context Engineering Phase 4
- 结构化短期记忆与 rolling summary 能力形成雏形
- 为 `app/rag/` / 长期记忆预留清晰边界

---

## 7. 当前阶段的新增工程目标：Infra 运行时标准化

在 Phase 3 中，除了持久化短期记忆本身，还需要正式纳入一项工程目标：

### 7.1 目标
建立 `infra/` 目录，统一管理：

- app 容器构建
- Redis 容器依赖
- Docker Compose 联调
- 环境变量样例
- 本地运行方式说明

### 7.2 价值
- 避免“作者电脑能跑，别处不能跑”
- 让 Phase 3 的 Redis 依赖可复现
- 为后续测试环境、CI、部署方式打基础
- 保持运行方式治理与业务代码边界分离

### 7.3 当前边界
本阶段只做：
- 本地开发/联调/演示级 Docker 化
- app + redis compose 编排

本阶段不做：
- Kubernetes
- 生产级容器平台
- 复杂镜像矩阵
- 多环境发布系统
- 高可用 Redis 编排

### 7.4 当前状态（2026-04-08）

`infra/` 已完成最小可用落地，当前包含：

- `infra/Dockerfile`
- `infra/compose.yaml`
- 根目录 `.env.example`（当前阶段唯一配置文件）
- `infra/README.md`

用于本地一键启动 app + redis 并联调 Phase 3 持久化短期记忆路径。
当前阶段代码与 compose 均直接读取根目录 `.env.example`，不再使用 `.env`，且本轮不处理 API key 安全治理。

---

## 8. 当前阶段不建议做的事情

1. 提前新增大量未来目录
2. 过早把系统拆成过多抽象层
3. 为没有需求的能力设计复杂框架
4. 在没有文档约束前大规模重构
5. 在模块边界不清晰时继续快速叠功能
6. 把 Phase 3 直接做成长期记忆或 RAG 工程
7. 把 Docker / infra 做成新的业务层

---

## 9. 项目推进方式

项目建议按以下方式推进：

1. 先固化文档体系
2. 再校正目录与分层
3. 再稳定主链路
4. 再增强 provider / prompt / context
5. 再标准化运行时基础设施
6. 最后再考虑新增系统能力

在当前轮次中继续沿用这一节奏：

1. 先升级根目录文档
2. 再升级目标模块 `AGENTS.md`
3. 再升级必要的 skill / checklist / test matrix
4. 再落地 Redis/store/config/manager/service/API 代码
5. 再落地 `infra/` Docker / compose 代码
6. 最后补测试与文档回写

---

## 10. 里程碑定义

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

### M4-C-Infra：Phase 3 运行时基础设施完成
- `infra/` 目录建立
- app + redis Docker / compose 可用
- 环境变量样例可用
- 本地联调方式可复现

### M4-D：Context Engineering Phase 4 完成
- 结构化短期记忆与 rolling summary 能力形成雏形
- 为 `app/rag/` / 长期记忆预留清晰边界

### M5：扩展能力准备完成
- 可以有序引入 RAG / Agent 等新模块，而不破坏现有体系

---

## 11. 一句话总结

本项目当前的核心计划不是“快速堆功能”，而是先完成**文档治理、结构治理、主链路稳定化、AI 能力基础设施固化和运行时基础设施标准化**。  
Phase 2 已让请求时上下文治理成型；Phase 3 已将短期会话能力升级为持久化 session memory；当前新增的 `infra/` 则负责把 app + redis 的本地运行方式正式纳入治理。

---

## 12. 文档驱动闭环计划

从当前轮次开始，项目执行模式固定为：

`根目录文档 -> 模块 AGENTS -> 对应 skill -> 代码实现 -> review -> 文档回写`

### 里程碑门禁

- 没有完成文档链路定义，不进入代码改动
- 没有完成模块-skill 映射，不进入大于单文件的重构
- 没有完成回写检查，不允许视为任务完成

### Phase 3 专项门禁

- 未定义持久化 store contract 与配置边界，不进入持久化实现
- 未明确 `ContextStorageConfig` 与 `ContextPolicyConfig` 的职责分离，不进入配置改造
- 未明确 session TTL 与 reset 语义，不进入 Redis store 开发
- 未更新文档与 skill，不上线持久化短期记忆能力

### Infra 专项门禁

- 未定义 `infra/` 的职责边界，不进入 Docker / compose 开发
- 未明确 app 与 redis 的运行方式，不进入 compose 编排
- 未明确环境变量来源与默认值，不进入 Docker 镜像固化
