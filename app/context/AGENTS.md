# app/context/AGENTS.md

> 更新日期：2026-04-10

## 1. 文档定位

本文件定义 `app/context/` 的职责、边界、结构约束、开发约束与 review 标准。
当前阶段，本文件临时同时承担该模块的 `AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW` 职责。
执行 context 相关任务时，必须先读根目录 `AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md`，再读本文件，再根据 skill `skills/python-context-capability/` 执行。

本文件不负责：

- 仓库级协作规则
- 你和我之间的交互流程
- 根目录阶段路线图
- 根目录级总体架构说明
- 根目录级 Code Review 总标准

这些内容分别由：

- 根目录 `AGENTS.md`
- 根目录 `PROJECT_PLAN.md`
- 根目录 `ARCHITECTURE.md`
- 根目录 `CODE_REVIEW.md`
- `CHAT_HANDOFF.md`

承担。

---

## 2. 模块定位

`app/context/` 是系统的短期会话上下文与短期记忆治理层。
它负责 provider-agnostic 的 conversation-scoped 状态表示、策略执行、store 抽象与会话生命周期管理。

当前已完成：

- Phase 2：token-aware context pipeline
- Phase 3：持久化短期记忆
- Phase 4：layered short-term memory

当前目录下已有实现：

- `models.py`
- `manager.py`
- `memory_reducer.py`
- `rendering.py`
- `policies/`
- `stores/`
- `__init__.py`

当前阶段必须兼容：

- **Phase 5：Streaming Chat & Conversation Lifecycle**
- **Phase 6：Knowledge + Citation Layer 的后续接入**

---

## 3. 本模块职责

1. 定义 canonical context models
2. 定义并实现 store contract 与 store adapter
3. 通过 `ContextManager` 暴露统一 façade
4. 管理 recent raw / rolling summary / working memory
5. 管理 message lifecycle 相关状态字段
6. 管理 completed 态的标准 memory update
7. 为 request assembly 提供安全、稳定的会话短期状态输入

---

## 4. 本模块不负责什么

1. 不负责 HTTP 路由
2. 不负责同步或流式 chat 主链路编排
3. 不负责 provider payload 协议
4. 不负责 SSE 文本协议
5. 不负责 RAG、向量检索、长期记忆、用户画像
6. 不负责 parser / chunker / embedding / index / retrieval
7. 不负责外部事件顺序决策

---

## 5. 依赖边界

### 允许依赖
- `app/schemas/`（如需要共享基础契约）
- `app/observability/`

### 禁止依赖
- `app/api/`
- `app/services/`
- `app/providers/`
- `app/rag/`

### 原则
`app/context/` 是会话短期状态层，不是主链路编排层，也不是知识检索层。

---

## 6. 架构原则

### 6.1 context 只管理 short-term memory
Phase 4 已建立：
- recent raw messages
- rolling summary
- structured working memory

这些能力在 Phase 5 / Phase 6 继续保持不变。

### 6.2 context 不等于 RAG
Phase 6 新增的 retrieval / knowledge block / citations 属于 `app/rag/` 与 `app/services/` 的协作结果，
不属于 `app/context/` 的职责范围。

### 6.3 completed 才进入标准 memory update
必须继续保持：
- completed：走标准 update pipeline
- failed / cancelled：只更新消息状态，不进入标准 memory update
- delta：只做流式过程状态更新

### 6.4 non-completed assistant message 不进入后续装配
request assembly 仍只能使用 completed assistant message 参与后续上下文组装。

### 6.5 retrieval 不替代 short-term memory
Phase 6 中引入的知识检索是外部 grounding，不得把 retrieval 结果视为 working memory 或 rolling summary 的一部分。

---

## 7. 当前阶段能力声明

当前本轮必须保持稳定：

- conversation-scoped context
- recent raw / rolling summary / working memory 三层结构
- assistant message lifecycle 状态落盘
- completed 才触发标准 memory update
- non-completed assistant message 不参与后续 request assembly
- `InMemoryContextStore` / `RedisContextStore`
- `selection -> truncation -> deterministic summary -> serialization` 策略链
- `RuleBasedWorkingMemoryReducer`

当前本轮必须兼容：

- `/chat` 当前的 request assembly
- `/chat_stream` 的 completed / failed / cancelled 收口
- 后续 retrieval 引入后 context 语义不被污染

当前本轮不要求在 `context` 中新增：

- 知识对象模型
- 文档切块
- embedding
- vector retrieval
- citation 生成

---

## 8. 文档维护规则（强约束）

本文件属于 `app/context/` 模块的治理模板资产。
后续任何更新，必须严格遵守以下规则：

### 8.1 基线规则
- 必须以当前文件内容为基线进行增量更新
- 不涉及变动的内容不得改写
- 未经明确确认，不得重写文件整体风格

### 8.2 冻结规则
未经明确确认，不得擅自改变以下内容：

- 布局
- 排版
- 标题层级
- 写法
- 风格
- 章节顺序

### 8.3 允许的修改范围
允许的修改仅包括：

1. 在原有章节内补充当前阶段内容
2. 新增当前阶段确实需要的新章节
3. 更新日期、阶段、默认基线等必要信息
4. 删除已明确确认废弃且必须移除的旧约束

### 8.4 禁止事项
禁止：

1. 把原文档整体改写成另一种风格
2. 把模块文档从“模块治理文件”改写成“泛项目说明书”
3. 每次更新都擅自改变标题层级与章节结构
4. 未经确认新增大段不属于本模块职责的内容

### 8.5 模板升级规则
如果未来需要升级 `app/context/AGENTS.md` 的模板，必须先明确说明这是一次“模板升级”，并在确认后再统一应用。
在未确认是“模板升级”前，默认只允许做增量更新，不允许重写模板。

---

## 9. 修改规则

1. 不允许 context 层依赖 API route 或 StreamingResponse
2. 不允许 context 层依赖 provider SDK
3. 不允许把流式事件顺序逻辑写进 context 层
4. 不允许在 delta 阶段执行标准 layered memory 更新
5. `ContextWindow.messages` 仍只表示 recent raw messages
6. 不允许把 retrieval 结果直接写入 working memory 或 rolling summary

---

## 10. Code Review 清单

1. canonical model 是否清晰表达 message lifecycle？
2. store codec 是否正确序列化 / 反序列化 lifecycle 字段？
3. non-completed assistant message 是否默认被过滤？
4. completed 态是否才进入标准 memory update？
5. 是否破坏 Phase 2 policy pipeline？
6. 是否把流式业务编排错误地下沉到 context 层？
7. 是否没有把 retrieval、citation、知识块语义混入 context？
8. 本次文档更新是否遵守了“文档维护规则”？
9. 是否保持了原有布局、排版、标题层级、写法和风格？

---

## 11. 测试要求

至少覆盖：

1. conversation scope 隔离
2. lifecycle 字段序列化 / 反序列化
3. placeholder -> completed / failed / cancelled
4. non-completed assistant message 不参与 request assembly
5. completed 才触发 layered memory 更新
6. reset_session / reset_conversation 在持久化 store 上行为正确
7. `build_context_store` 的内存 / Redis 选择行为正确
8. 引入 retrieval 后，Phase 4 / Phase 5 原有上下文行为仍保持稳定

---

## 12. 一句话总结

`app/context/` 在当前阶段不是流式交付层，也不是知识增强层，而是为同步会话、流式会话和 Phase 6 知识增强提供安全、稳定的 conversation-scoped 状态模型与 completed 态记忆收口规则，并在后续更新中严格遵守模块文档的模板冻结规则。
