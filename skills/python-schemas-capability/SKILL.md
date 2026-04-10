# SKILL.md

> skill_name: python-schemas-capability
> module_scope: app/schemas/
> status: active
> last_updated: 2026-04-10

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `app/schemas/` 模块中进行内部规范化 LLM 契约的设计、实现、测试与增量演进。

本 skill 的目标不是生成“泛化的数据类示例”，而是约束在本项目文档治理体系下，按当前仓库真实代码结构实现：

- `LLMMessage`
- `LLMRequest`
- `LLMUsage`
- `LLMResponse`
- `LLMStreamChunk`

---

## 2. Skill 适用范围

本 skill 适用于以下类型的工作：

1. `llm_request.py`
2. `llm_response.py`
3. 内部 LLM canonical contract 调整
4. dataclass 校验与字段语义维护
5. schema 相关测试

---

## 3. Skill 不适用范围

本 skill 不用于以下工作：

1. API request / response schema
2. SSE 事件 payload schema
3. cancel / reset contract
4. chat 主链路编排
5. retrieval / chunking / embedding / index 实现
6. citation contract
7. metrics / tracing / observability 平台
8. 审批流
9. Case Workspace

如任务超出上述边界，应转交对应模块 skill 处理。

---

## 4. 本 skill 的核心原则

### 4.1 内部 canonical contract 优先
`app/schemas/` 当前服务于 service 与 provider 之间的共享契约，不承接 API 对外契约。

### 4.2 API 契约与内部契约分离
当前 `/chat`、`/chat_stream`、cancel、reset 相关 Pydantic 模型位于 `app/api/schemas/`。
不得把两套职责混写。

### 4.3 provider-agnostic
`LLM*` 契约必须屏蔽厂商差异，不直接泄漏 SDK 原始对象。

### 4.4 流式与非流式语义一致
`finish_reason`、`usage`、`metadata` 等核心语义在 `LLMResponse` 与 `LLMStreamChunk` 中必须保持一致。

### 4.5 citation schema 继续与内部契约分离
citation schema 已在 `app/api/schemas/` 落地，不得写进 `app/schemas/` 的默认基线。

---

## 5. 默认阶段基线

当前 skill 默认基线如下：

- `LLMMessage` 负责 role / content
- `LLMRequest` 负责 provider / model / messages / metadata 等输入字段
- `LLMUsage` 负责 token usage
- `LLMResponse` 负责同步 canonical result
- `LLMStreamChunk` 负责流式 canonical chunk
- API 对外契约当前不在本模块

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
   - `skills/python-schemas-capability/SKILL.md`

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

1. `LLMMessage` / `LLMRequest` 更新
2. `LLMUsage` / `LLMResponse` 更新
3. `LLMStreamChunk` 更新
4. schema 相关测试更新

仅给概念说明、不落代码、不补测试，不视为完成。

---

## 8. 实现约束

### 8.1 命名约束
字段名必须稳定、可读、可推断语义。

### 8.2 边界约束
不得把 API 对外字段、citation 或 retrieval 内部对象塞进当前 `LLM*` 契约。

### 8.3 校验约束
`role`、`temperature`、`max_tokens` 等字段校验必须保持清晰且可测试。

### 8.4 兼容性约束
schema 改动必须谨慎处理兼容性，不得轻易破坏 service / provider / tests 既有用法。

### 8.5 扩展约束
未来如确有需要新增内部共享模型，必须先明确它属于内部 canonical contract，而不是 API 对外 contract。

---

## 9. 与其他模块的协作约束

### 与 api 协作
API 有自己的 schema 子模块。
`app/schemas/` 不直接接管 API 对外契约。

### 与 services 协作
services 消费 `LLM*` 契约进行编排，但不应各自发明新的内部 canonical contract。

### 与 providers 协作
providers 输出 canonical result / chunk，并通过 `LLM*` 契约与 services 协作。

### 与 rag 协作
当前 `app/schemas/` 不承接 rag 的 citation / retrieval 模型。

---

## 10. 测试要求

schemas 相关实现至少补以下测试之一或多项：

1. `LLMMessage` 角色校验
2. `LLMRequest` 字段归一化
3. `temperature` / `max_tokens` 校验
4. `LLMResponse` / `LLMUsage` 结构稳定性
5. `LLMStreamChunk` 字段语义稳定性
6. provider / service / request assembler 回归兼容性

---

## 11. Review 要点

提交前至少自查：

1. `app/schemas/` 是否仍然只做内部 canonical contract？
2. 是否没有把 API 对外 schema 混进来？
3. 是否没有把 retrieval / citation 对象混进来？
4. 流式与非流式语义是否一致？
5. 是否补了测试？

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

本 skill 的目标，是确保 `app/schemas/` 在当前项目中持续作为内部规范化 LLM 契约层演进，稳定承接 provider 与 service 之间的 `LLM*` 数据表达，而不是误写成 API / citation / cancel / reset 的综合契约目录。
