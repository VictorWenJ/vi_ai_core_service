# SKILL.md

> skill_name: python-observability-capability
> module_scope: app/observability/
> status: active
> last_updated: 2026-04-10

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `app/observability/` 模块中进行结构化日志基础设施的设计、实现、测试与增量演进。

本 skill 的目标不是生成“泛化日志工具”，而是约束在本项目文档治理体系下，按当前仓库真实代码结构实现：

- `log_report`
- JSON-safe 序列化
- request / stream / context / provider 相关事实型日志

---

## 2. Skill 适用范围

本 skill 适用于以下类型的工作：

1. `log_until.py`
2. `log_report`
3. JSON-safe 序列化辅助
4. observability 相关测试
5. 调试辅助输出与日志字段组织

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
会进入结构化日志的对象必须可安全序列化。

### 4.3 不能因为观测破坏主链路
observability 是支撑层，不得因为日志报错而打断同步或流式主链路。

### 4.4 当前代码的观测重点是主链路与组装过程
当前代码中，观测重点包括 request / stream / context assembly / provider 调用 / retrieval 生命周期。

### 4.5 日志不是状态存储
日志用于排查，不用于替代数据库、上下文 store 或正式契约。

---

## 5. 默认阶段基线

当前 skill 默认基线如下：

- 结构化日志为主
- JSON-safe 序列化
- `log_report` 为核心入口
- 当前不建设 tracing / metrics 平台
- 当前包含 retrieval / citation 专项可观测性

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

1. `log_report` 更新
2. JSON-safe 序列化更新
3. 事实型日志字段更新
4. observability 相关测试更新

仅给概念说明、不落代码、不补测试，不视为完成。

---

## 8. 实现约束

### 8.1 日志字段约束
字段命名必须稳定、可检索、可理解。

### 8.2 序列化约束
复杂对象必须优先投影为基础 dict / list / str / number / bool。

### 8.3 隐私约束
- 不输出不必要原文
- 不输出超大正文
- 不输出敏感内容明文

### 8.4 非入侵约束
不得为了“记录更多”而侵入主链路职责边界。

### 8.5 Phase 6 约束
当前代码已落地 retrieval / citation 观测；
新增字段必须与真实代码保持一致。

---

## 9. 与其他模块的协作约束

### 与 services 协作
services 决定何时记录什么；observability 提供记录能力。

### 与 api 协作
API 可调用 observability 输出协议相关事实，但 observability 不承担 API 协议实现。

### 与 context 协作
context 可记录 lifecycle 与 memory 相关事实，但 observability 不承担状态管理。

### 与 providers 协作
providers 可记录厂商调用与错误映射事实，但 observability 不承担 provider 调用逻辑。

### 与 rag 协作
当前代码中 rag 已落地运行时代码。
RAG 观测字段需按真实代码持续补充。

---

## 10. 测试要求

observability 相关实现至少补以下测试之一或多项：

1. JSON-safe 序列化测试
2. dataclass / pydantic / dict / list 输入归一化测试
3. 未知复杂对象退化为字符串测试
4. 流式场景不崩溃测试

---

## 11. Review 要点

提交前至少自查：

1. 是否仍然只是基础设施层？
2. 是否没有把业务逻辑混入 observability？
3. 是否保证 JSON-safe？
4. 是否避免了敏感正文泄漏？
5. retrieval / citation 观测字段是否与代码一致？
6. 是否补了测试？

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

本 skill 的目标，是确保 `app/observability/` 在当前项目中持续作为结构化日志基础设施层演进，以 `log_report` 和 JSON-safe 序列化支撑已落地主链路与 retrieval 生命周期观测。
