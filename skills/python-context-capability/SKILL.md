# SKILL.md

> skill_name: python-context-capability  
> module_scope: app/context/  
> status: active  
> last_updated: 2026-04-10

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `app/context/` 模块中进行短期会话上下文能力（Context Engineering）的设计、实现、测试与增量演进。

本 skill 的目标不是生成“泛化的上下文管理示例代码”，而是约束在本项目文档治理体系下，按企业级 AI 应用的标准实现：

- conversation-scoped 状态治理
- layered short-term memory
- message lifecycle 状态管理
- completed 态 memory update
- 与流式会话、知识增强兼容的上下文基础能力

---

## 2. Skill 适用范围

本 skill 适用于以下类型的工作：

1. `app/context/models.py` 相关模型设计与实现
2. `ContextManager` 设计与实现
3. `stores/*` store contract 与 store adapter
4. context codec / serialization
5. recent raw / rolling summary / working memory 治理
6. message lifecycle 字段扩展与状态收口
7. non-completed assistant message 过滤逻辑
8. context 相关测试与持久化测试

---

## 3. Skill 不适用范围

本 skill 不用于以下工作：

1. HTTP 路由设计
2. SSE 文本协议
3. chat 主链路编排
4. retrieval / chunking / embedding / index 实现
5. provider 主链路实现
6. citation 生成逻辑
7. 长期记忆平台
8. Agent Runtime
9. 审批流
10. Case Workspace

如任务超出上述边界，应转交对应模块 skill 处理。

---

## 4. 本 skill 的核心原则

### 4.1 Phase 2 policy pipeline 不变
默认策略顺序固定为：

`selection -> truncation -> deterministic summary -> serialization`

不允许无明确确认直接改动主顺序。

### 4.2 `ContextWindow.messages` 仍只表示 recent raw messages
在 Phase 4 / 5 / 6 中，该语义不变。  
不得把全部历史、retrieval 结果或 citations 混入该字段。

### 4.3 only completed assistant message 才进入标准 memory update
- completed：进入标准 update pipeline
- created / streaming / failed / cancelled：不进入标准 memory update

### 4.4 delta 阶段不得触发标准 rolling summary / working memory 更新
流式输出过程中，只能更新过程状态，不能提前污染 layered memory。

### 4.5 retrieval 不属于 context
Phase 6 引入的 retrieval / knowledge block / citations 属于外部知识增强，不属于 short-term memory。

---

## 5. 默认阶段基线

当前 skill 默认基线如下：

- conversation scope：`session_id + conversation_id`
- layered short-term memory：
  - recent raw
  - rolling summary
  - working memory
- lifecycle 字段：
  - `message_id`
  - `role`
  - `content`
  - `status`
  - `created_at`
  - `updated_at`
  - `finish_reason`
  - `error_code`
  - `metadata`
- only completed assistant message 进入标准 memory update
- non-completed assistant message 默认不参与 request assembly

如需变更该基线，必须先更新根目录文档与模块 AGENTS，再进入实现。

---

## 6. 标准执行流程

执行 `app/context/` 相关任务时，必须遵循以下顺序：

1. 阅读根目录文档  
   - `AGENTS.md`
   - `PROJECT_PLAN.md`
   - `ARCHITECTURE.md`
   - `CODE_REVIEW.md`

2. 阅读模块文档  
   - `app/context/AGENTS.md`

3. 阅读本 skill  
   - `skills/python-context-capability/SKILL.md`

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

context 相关任务，至少应交付以下之一或多项：

1. canonical context model 更新
2. manager / facade 更新
3. store contract / adapter 更新
4. lifecycle 状态字段更新
5. serialization / codec 更新
6. request assembly 过滤辅助更新
7. context 相关测试更新

仅给概念说明、不落代码、不补测试，不视为完成。

---

## 8. 实现约束

### 8.1 canonical model 约束
必须显式区分：
- `ContextWindow`
- `ContextMessage`
- `RollingSummaryState`
- `WorkingMemoryState`

不得用“大 dict 到处传”替代清晰模型。

### 8.2 store 约束
- store contract 必须稳定
- codec 必须覆盖 lifecycle 字段
- in-memory / redis 语义必须尽量一致

### 8.3 lifecycle 约束
必须清晰支持：
- placeholder
- streaming
- completed
- failed
- cancelled

但只有 completed 进入标准 memory update。

### 8.4 compatibility 约束
引入 retrieval 后，context 仍然只负责 short-term memory。  
不得因为 Phase 6 而把知识增强语义写进 context。

### 8.5 update 约束
- delta 阶段不得触发标准 layered memory 更新
- failed / cancelled 不进入标准 memory update
- completed 后才走正式收口逻辑

---

## 9. 与其他模块的协作约束

### 与 services 协作
`services` 负责编排；`context` 负责状态与记忆收口。  
`context` 不编排 chat / stream 主链路。

### 与 api 协作
API 不应直接操作 context manager。  
context 通过 service 暴露给 API。

### 与 rag 协作
`rag` 负责外部知识增强；`context` 负责短期会话记忆。  
两者不得互相替代。

### 与 providers 协作
provider 负责模型厂商适配；`context` 不直接依赖 provider SDK。

---

## 10. 测试要求

context 相关实现至少补以下测试之一或多项：

1. conversation scope 隔离测试
2. lifecycle 字段序列化 / 反序列化测试
3. placeholder / completed / failed / cancelled 状态测试
4. request assembly 过滤 non-completed assistant message 测试
5. completed 才进入 layered memory 更新测试
6. reset_session / reset_conversation 测试
7. redis store / in-memory store 一致性测试

---

## 11. Review 要点

提交前至少自查：

1. `ContextWindow.messages` 语义是否仍然正确？
2. only completed assistant message 是否才进入标准 memory update？
3. lifecycle 字段是否完整、可序列化？
4. 是否没有把 retrieval / citation / knowledge block 语义混进 context？
5. 是否补了测试？
6. 是否破坏了 Phase 2 / Phase 4 / Phase 5 已有语义？

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

本 skill 的目标，是确保 `app/context/` 在当前项目中以企业级、可增量演进、可测试、可审查的方式维持 conversation-scoped short-term memory 能力，并在 Phase 5 / Phase 6 中稳定承接 message lifecycle、completed 态记忆收口与 request assembly 过滤规则，而不是演化成承担 retrieval 或 chat 编排职责的模块。