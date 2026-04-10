# SKILL.md

> skill_name: python-observability-capability  
> module_scope: app/observability/  
> status: active  
> last_updated: 2026-04-10

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `app/observability/` 模块中进行可观测性基础设施的设计、实现、测试与增量演进。

本 skill 的目标不是生成“泛化日志工具”，而是约束在本项目文档治理体系下，按企业级 AI 应用的标准实现：

- 结构化日志
- JSON-safe 序列化
- request / stream / retrieval 关键字段观测
- 与同步、流式、知识增强链路兼容的事实型记录能力

---

## 2. Skill 适用范围

本 skill 适用于以下类型的工作：

1. 结构化日志工具函数
2. JSON-safe 序列化辅助
3. request / stream / lifecycle 观测字段补充
4. retrieval / citation 观测字段补充
5. observability 相关测试
6. 调试辅助输出与日志字段组织

---

## 3. Skill 不适用范围

本 skill 不用于以下工作：

1. chat 主链路编排
2. SSE 事件协议定义
3. context state 更新
4. retrieval / chunking / embedding / index 实现
5. provider SDK 调用
6. citation 生成
7. metrics / tracing / alerting 平台建设
8. 审批流
9. Case Workspace

如任务超出上述边界，应转交对应模块 skill 处理。

---

## 4. 本 skill 的核心原则

### 4.1 只记录事实，不记录业务推理
日志应记录“发生了什么”，而不是“系统为什么这么想”。

### 4.2 JSON-safe 是硬约束
任何会进入结构化日志的对象都必须可安全序列化。  
不可直接写入：
- threading.Event
- lock
- generator
- 复杂 SDK 对象
- 未处理的 dataclass 深层对象

### 4.3 不能因为观测破坏主链路
observability 是支撑层，不得因为日志报错、字段序列化失败而打断同步或流式主链路。

### 4.4 retrieval 是 Phase 6 观测重点
必须支持定位：
- 是否启用了 retrieval
- retrieval query 是什么
- top-k / filters 是什么
- 命中了多少 chunk / document
- citations 结果如何

### 4.5 日志不是状态存储
日志用于排查，不用于替代数据库、上下文 store、取消注册表或正式契约。

---

## 5. 默认阶段基线

当前 skill 默认基线如下：

- 结构化日志为主
- JSON-safe 序列化
- request / stream / context / retrieval 关键字段可观测
- retrieval / citation 观测在 Phase 6 中补齐
- 不建设完整 tracing / metrics 平台

如需变更该基线，必须先更新根目录文档与模块 AGENTS，再进入实现。

---

## 6. 标准执行流程

执行 `app/observability/` 相关任务时，必须遵循以下顺序：

1. 阅读根目录文档  
   - `AGENTS.md`
   - `PROJECT_PLAN.md`
   - `ARCHITECTURE.md`
   - `CODE_REVIEW.md`

2. 阅读模块文档  
   - `app/observability/AGENTS.md`

3. 阅读本 skill  
   - `skills/python-observability-capability/SKILL.md`

4. 按需阅读 assets / references  
   - `assets/capability-scope.md`
   - `assets/delivery-workflow.md`
   - `assets/acceptance-checklist.md`
   - `references/module-boundaries.md`
   - `references/data-contracts.md`
   - `references/testing-matrix.md`

5. 明确本轮任务边界  
6. 设计最小增量改动  
7. 补充测试  
8. 自检与回归验证

---

## 7. 标准交付物要求

observability 相关任务，至少应交付以下之一或多项：

1. 结构化日志工具更新
2. JSON-safe 序列化更新
3. request / stream 字段更新
4. retrieval / citation trace 字段更新
5. observability 相关测试更新

仅给概念说明、不落代码、不补测试，不视为完成。

---

## 8. 实现约束

### 8.1 日志字段约束
字段命名必须稳定、可检索、可理解。  
不得同一个概念用多个名字来回变化。

### 8.2 序列化约束
必须优先将复杂对象投影为：
- 基础 dict
- 基础 list
- 基础字符串 / 数字 / 布尔值

不得直接记录复杂运行时对象。

### 8.3 retrieval 约束
至少支持以下事实字段：
- retrieval_query
- retrieval_top_k
- retrieval_filters
- retrieved_chunk_count
- retrieved_document_ids
- citation_count
- embedding_model
- vector_index_backend

### 8.4 隐私约束
- 不输出不必要原文
- 不输出超大正文
- 不输出敏感内容明文
- 必要时用摘要或统计替代原文

### 8.5 非入侵约束
不得为了“记录更多”而侵入主链路职责边界。

---

## 9. 与其他模块的协作约束

### 与 services 协作
services 决定何时记录什么；observability 提供记录能力。  
observability 不替代 service 决策。

### 与 api 协作
API 可调用 observability 输出协议相关事实，但 observability 不承担 API 协议实现。

### 与 context 协作
context 可记录 lifecycle 与 memory 相关事实，但 observability 不承担 context 状态管理。

### 与 rag 协作
rag 可记录 ingestion / retrieval / citation 相关事实，但 observability 不承担 retrieval 实现。

### 与 providers 协作
providers 可记录厂商调用与错误映射事实，但 observability 不承担 provider 调用逻辑。

---

## 10. 测试要求

observability 相关实现至少补以下测试之一或多项：

1. JSON-safe 序列化测试
2. request trace 字段测试
3. stream trace 字段测试
4. retrieval trace 字段测试
5. citation_count 字段测试
6. 不可序列化对象保护测试
7. 流式场景不崩溃测试

---

## 11. Review 要点

提交前至少自查：

1. 是否仍然只是基础设施层？
2. 是否没有把业务逻辑混入 observability？
3. 是否保证 JSON-safe？
4. retrieval / citation 相关字段是否齐全？
5. 是否避免了敏感正文泄漏？
6. 是否补了测试？
7. 是否没有破坏同步或流式主链路？

---

## 12. 关联文件

- `assets/capability-scope.md`
- `assets/delivery-workflow.md`
- `assets/acceptance-checklist.md`
- `references/module-boundaries.md`
- `references/data-contracts.md`
- `references/testing-matrix.md`

---

## 13. 一句话总结

本 skill 的目标，是确保 `app/observability/` 在当前项目中以企业级、可增量演进、可测试、可审查的方式为同步聊天、流式聊天、上下文工程与 Phase 6 知识增强提供结构化、JSON-safe、事实型的可观测性能力，而不是演化成承担业务决策的辅助服务层。