---
name: python-ai-provider-capability
description: 用于在 Python 项目中重构或新增外部 AI Provider 集成。覆盖 LLM、图像生成、视频生成、音频、embedding、reranker 等类型。重点用于 provider 抽象、请求/响应归一化、service 层解耦、配置外置化与聚焦式结构重构。不用于 RAG 编排、Agent 逻辑、工作流引擎、数据库或无关重构。
last_updated: 2026-04-06
---

# 目的

本 Skill 用于统一本仓库中与 Provider 相关的重构方式。

它适用于所有 Provider 类型，包括：
- 文本 / LLM Provider
- 图像生成 Provider
- 视频生成 Provider
- 音频 Provider
- Embedding Provider
- Reranker Provider
- 未来新增的外部 AI 能力 Provider

目标是确保所有 Provider 集成遵循一致工程规则：
- 厂商隔离
- Schema 归一化
- Service 层解耦
- 配置外置化
- 显式错误处理
- 清晰架构边界

# 当前阶段约束（必须遵守）

在 `vi_ai_core_service` 当前基础设施阶段，使用本 Skill 必须严格限制范围：

- 仅稳定当前主链路使用的非流式 LLM Provider 路径。
- streaming、多模态、tools/function calling、structured output 以及非 LLM Provider 家族能力均为后续阶段预留。
- 不引入重型 Provider 平台（路由引擎、fallback 框架、能力协商系统等）。
- 优先保证边界正确、契约归一化与可测试行为。

# 何时使用本 Skill

在以下场景使用本 Skill：
- 将 demo 风格的外部 AI 调用收敛为 Provider 结构
- 在现有架构下新增外部 Provider
- 隔离 SDK/API 厂商细节
- 统一请求与响应模型
- 将 Provider 逻辑从脚本或业务模块迁出
- 提升 Provider 相关代码可维护性

# 不适用场景

本 Skill 不用于：
- RAG Pipeline 实现
- Agent 逻辑
- 工作流引擎设计
- 后台任务系统
- 数据库设计
- 队列系统设计
- 无关清理或大范围架构重写

# 必须执行流程

始终按以下顺序执行：

1. 理解当前结构
2. 识别 Provider 相关耦合点
3. 给出最小重构方案
4. 仅实施符合当前阶段边界的最小 Provider 改动
5. 执行验证与边界检查
6. 报告改动文件、运行步骤、验证步骤与文档回写情况

# 重构规则

## 1. 保持 Provider 逻辑隔离
厂商 SDK/API 细节必须留在 Provider 模块内部。

## 2. 规范边界
业务层与 Service 层不应直接依赖厂商 SDK 原始类型。

## 3. 保持结构稳定
优先采用或保持如下目录结构：
- `providers/`
- `schemas/`
- `services/`
- `core/config/`

## 4. 控制改动范围
不要把无关重构混入 Provider 任务。

## 5. 保持可扩展性
改动结果应让未来新增 Provider 更容易。

## 6. 配置外置化
不要硬编码：
- 密钥
- 环境相关 URL
- 本应配置化的厂商运行参数

## 7. 预留执行模型差异
不同 Provider 可能存在：
- 同步 vs 异步执行
- 流式 vs 非流式
- 直接返回 vs 任务轮询
- 文本 vs 文件/媒体输出

必须为这些差异保留扩展点。

# 编码前预期输出

编码前应给出：
- 任务理解
- 范围界定
- 假设条件
- 文件级改动计划
- 接口/类设计
- 可扩展性考虑
- 风险与权衡

# 编码后预期输出

编码后应给出：
- 改动文件列表
- 各文件改动内容
- 运行方式
- 验证方式
- 下一步最小增量建议

# 资产与验证索引

1. Checklist：`assets/ai_provider_capability_checklist.md`
2. Test Matrix：`assets/ai_provider_test_matrix.md`
3. References：`references/ai_provider_capability_boundary_and_acceptance.md`

# 治理链路

在 `vi_ai_core_service` 中执行本 Skill 时，必须遵循以下闭环：

`根目录文档 -> app/providers/AGENTS.md -> 本 skill -> 代码修改 -> review -> 文档回写`

必过门禁：

1. 未完成根目录文档与模块 `AGENTS.md` 阅读前，不得开始实现。
2. 改动后必须对照根 `CODE_REVIEW.md`、模块 `AGENTS.md` 与本 Skill checklist 自审。
3. 若 Provider 契约、边界或测试事实变化，必须在同一变更中同步更新相关文档与测试。

