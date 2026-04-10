# SKILL.md

> skill_name: python-schema-capability  
> module_scope: app/schemas/  
> status: active  
> last_updated: 2026-04-10

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `app/schemas/` 模块中进行共享契约层的设计、实现、测试与增量演进。

本 skill 的目标不是生成“泛化的数据类示例”，而是约束在本项目文档治理体系下，按企业级 AI 应用的标准实现：

- API request / response contract
- stream event payload contract
- cancel / reset contract
- lifecycle contract
- Phase 6 citation contract
- 其他跨模块共享的数据表达

---

## 2. Skill 适用范围

本 skill 适用于以下类型的工作：

1. `/chat` request / response schema 设计与实现
2. `/chat_stream` event payload schema 设计与实现
3. `/chat_stream_cancel` schema 设计与实现
4. `/chat_reset` schema 设计与实现
5. lifecycle 相关 schema 设计与实现
6. citation 相关 schema 设计与实现
7. schema 相关测试

---

## 3. Skill 不适用范围

本 skill 不用于以下工作：

1. HTTP 路由设计
2. chat 主链路编排
3. context store 实现
4. provider SDK 适配
5. retrieval / chunking / embedding / index 实现
6. citation 生成逻辑
7. metrics / tracing / observability 平台
8. 审批流
9. Case Workspace

如任务超出上述边界，应转交对应模块 skill 处理。

---

## 4. 本 skill 的核心原则

### 4.1 契约优先
共享数据表达应先形成清晰 schema，再被 API / service / provider / rag 等模块消费。

### 4.2 共享契约不等于内部对象直透
内部对象、原始 SDK 响应、检索对象、状态对象，不应未经收敛直接变成对外 schema。

### 4.3 同步与流式要有一致语义
`/chat` 与 `/chat_stream` 不要求字段完全一致，但应表达同一套业务语义。

### 4.4 citation 是正式 contract
Phase 6 的 citation 是正式共享契约，而不是 API 层临时拼接的字段。

### 4.5 当前阶段避免过度扩张 schema 范围
当前只治理：
- chat
- stream
- cancel
- reset
- lifecycle
- citation

不提前扩展到全量业务对象体系。

---

## 5. 默认阶段基线

当前 skill 默认基线如下：

- `/chat` request / response schema 稳定
- `/chat_stream` 事件 schema 稳定
- `/chat_stream_cancel` schema 稳定
- `/chat_reset` schema 稳定
- lifecycle 相关字段语义清晰
- Phase 6 citation contract 正式化
- delta 阶段不带 citations

如需变更该基线，必须先更新根目录文档与模块 AGENTS，再进入实现。

---

## 6. 标准执行流程

执行 `app/schemas/` 相关任务时，必须遵循以下顺序：

1. 阅读根目录文档  
   - `AGENTS.md`
   - `PROJECT_PLAN.md`
   - `ARCHITECTURE.md`
   - `CODE_REVIEW.md`

2. 阅读模块文档  
   - `app/schemas/AGENTS.md`

3. 阅读本 skill  
   - `skills/python-schema-capability/SKILL.md`

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

schemas 相关任务，至少应交付以下之一或多项：

1. request / response schema 更新
2. stream event schema 更新
3. cancel / reset schema 更新
4. lifecycle schema 更新
5. citation schema 更新
6. schema 相关测试更新

仅给概念说明、不落代码、不补测试，不视为完成。

---

## 8. 实现约束

### 8.1 命名约束
字段名必须稳定、可读、可推断语义。  
同一概念不得在不同 contract 中反复换名。

### 8.2 层级约束
schema 必须体现业务语义，而不是暴露内部实现层次。  
不要把内部模块结构直接映射为外部字段层级。

### 8.3 citation 约束
- `/chat` response 可带 citations
- `/chat_stream` completed event 可带 citations
- delta 阶段不带 citations
- citation 结构应为可展示结构，不是内部 retrieval 对象透传

### 8.4 lifecycle 约束
stream event、message lifecycle、finish_reason、error_code 等字段语义必须保持一致。

### 8.5 兼容性约束
schema 改动必须谨慎处理兼容性。  
不得轻易破坏已有主链路契约。

---

## 9. 与其他模块的协作约束

### 与 api 协作
API 通过 schema 表达 request / response / SSE payload。  
API 不应绕过 schema 临时拼字段。

### 与 services 协作
services 消费 schema 进行编排输出，但不应各自发明新的外部 contract。

### 与 providers 协作
providers 可有内部 canonical contract，但共享暴露给上层时必须经过 schema 收敛。

### 与 rag 协作
citation 最终进入共享 contract，但 retrieval 内部对象不应直接外泄。

### 与 context 协作
context lifecycle 字段如需进入共享契约，应由 schema 统一定义表达方式。

---

## 10. 测试要求

schemas 相关实现至少补以下测试之一或多项：

1. `/chat` request / response schema 测试
2. `/chat_stream` 事件 schema 测试
3. `/chat_stream_cancel` schema 测试
4. `/chat_reset` schema 测试
5. citation schema 测试
6. lifecycle 字段一致性测试
7. delta 不带 citations 的测试

---

## 11. Review 要点

提交前至少自查：

1. schemas 是否仍是共享契约层？
2. 是否没有把内部对象直接外泄？
3. `/chat` 与 `/chat_stream` 是否语义一致？
4. citations 是否正式进入共享 contract？
5. delta 是否没有 citations？
6. 是否补了测试？
7. 是否没有破坏已有主链路兼容性？

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

本 skill 的目标，是确保 `app/schemas/` 在当前项目中以企业级、可增量演进、可测试、可审查的方式统一管理共享契约层，特别是在 Phase 6 中正式承接 citation、stream event 与 chat response 的一致表达，而不是让各模块各自临时拼装 contract。