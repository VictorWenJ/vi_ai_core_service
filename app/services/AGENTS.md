# app/services/AGENTS.md

> 更新日期：2026-04-13

## 1. 文档定位

本文件定义 `app/services/` 的职责、边界、结构约束、开发约束与 review 标准。
当前阶段，本文件临时同时承担该模块的 `AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW` 职责。
执行 services 相关任务时，必须先读根目录 `AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md`，再读本文件，再根据 skill `skills/python-service-capability/` 执行。

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

`app/services/` 是系统的应用入口与 façade 层。
它负责承接外部 chat / chat_stream 请求，把用户请求映射为统一的 runtime 输入，并把 runtime 结果交付为同步 JSON 或 SSE 事件流。

当前阶段建议围绕以下职责组织：

- `chat_service.py`
- `streaming_chat_service.py`
- `request_assembler.py`
- `cancellation_registry.py`
- `prompt_service.py`
- `runtime_service.py`（若存在系统运行态摘要聚合）
- `errors.py`

其中，`ChatService` 与 `StreamingChatService` 继续存在，但不再承担主编排内核；主编排内核下沉到 `app/chat_runtime/`。

---

## 3. 本模块职责

1. 承接同步与流式两类会话用例入口
2. 把 API 请求模型转换为统一 runtime 请求
3. 调用 `chat_runtime` 的同步或流式执行入口
4. 管理 SSE 交付与 service 级错误收口
5. 继续协调 `CancellationRegistry` 等请求级配套能力
6. 对外提供清晰、稳定的应用层 service 入口
7. 对系统运行态摘要等跨模块信息提供面向消费者无关的应用层聚合（若当前阶段需要）

---

## 4. 本模块不负责什么

1. 不负责 HTTP 路由与 SSE 文本协议格式本身
2. 不负责 provider SDK / HTTP 适配细节
3. 不负责 context store 的底层存储实现
4. 不负责定义共享数据契约本身
5. 不负责 parser / chunker / embedding / index 的底层实现
6. 不负责向量库访问细节
7. 不负责 workflow / hook / step dispatch 主执行内核
8. 不负责 runtime skill loader、Tool Calling、Agent Runtime

---

## 5. 依赖边界

### 允许依赖
- `app/chat_runtime/`
- `app/context/`
- `app/prompts/`
- `app/providers/`
- `app/schemas/`
- `app/observability/`
- `app/api/schemas/`（当前代码中的用户请求入口模型）

### 禁止依赖
- `app/api/chat.py` 等路由实现
- Redis client、key 拼接、TTL 细节
- 向量库底层 SDK 作为常规业务编排路径直接散落在 service 层
- 重新在 service 层实现 workflow、hook、trace 统一调度

### 原则
`app/services/` 是 façade 层，不是协议层、不是状态层、不是知识实现层，也不是 chat runtime 主执行层。

---

## 6. 架构原则

### 6.1 façade 优先，编排下沉
services 负责入口适配与结果交付；主业务编排下沉到 `app/chat_runtime/`。

### 6.2 request_assembler 仍是上下文与知识装配中枢
assembler 是唯一允许决定以下顺序的地方：

1. system prompt
2. knowledge block
3. working memory block
4. rolling summary block
5. recent raw messages
6. current user input

### 6.3 lifecycle 业务语义由 chat_runtime 统一调度
API 不负责状态机；context 不负责流式业务编排；providers 不负责外部会话生命周期；services 也不再承担统一 lifecycle 调度内核。

### 6.4 completed 收口必须与 Phase 4 / Phase 5 对齐
- completed：执行标准 memory update
- failed / cancelled：只更新消息状态，不走标准 memory update
- delta：只负责传输与聚合，不写 rolling summary / working memory

### 6.5 当前代码已落地 retrieval 编排
- 当前 request assembly 已支持 knowledge block
- retrieval 失败时由 chat runtime 执行可控降级，不能散落到 API / provider / context / services

### 6.6 同步与流式必须共享同一套业务语义
- `/chat` 与 `/chat_stream` 的核心语义来自同一套 chat runtime workflow
- stream 只是交付方式不同，不应导致核心应用语义分裂

### 6.7 控制面聚合服务命名原则
- 面向控制台、CLI 或未来其他消费者的应用服务，命名应按领域职责或应用职责，而不是按当前消费者命名
- runtime summary / config summary / health 等系统摘要能力若需在应用层聚合，应位于 `app/services/` 这类应用入口层，而不是长期放在错误模块中
- `services` 可以承接消费者无关的应用级聚合，但不得演化为跨全系统的 God Service

---

## 7. 当前阶段能力声明

当前本轮必须保持稳定：

- 同步 chat 主链路对外入口
- 流式 chat 主链路对外入口
- cancellation registry
- request assembly
- SSE 交付与事件转发
- completed 才触发 context memory 标准更新
- failed / cancelled 不污染后续 request assembly
- started / delta / heartbeat / completed / error / cancelled 事件契约
- 同步主入口统一为 `chat_runtime.run_sync` 的 façade，流式主入口统一为 `chat_runtime.run_stream` 的 façade

当前代码事实补充：

- `ChatRequestAssembler` 当前装配顺序为：system -> knowledge -> working memory -> rolling summary -> recent raw -> user
- `ChatService` 当前负责编排同步聊天，但本轮目标是降级为 façade
- `StreamingChatService` 当前负责 placeholder、delta 聚合、取消注册、完成/异常收口，但本轮目标是降级为 façade + SSE 交付入口
- 当前代码已实现 retrieval 调用、knowledge block 注入与 citations 输出

当前本轮不要求：

- Tool Calling
- runtime skill loader
- Agentic workflow
- 审批流编排
- Case Workspace 业务流程编排

---

## 8. 文档维护规则（强约束）

本文件属于 `app/services/` 模块的治理模板资产。
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
如果未来需要升级 `app/services/AGENTS.md` 的模板，必须先明确说明这是一次“模板升级”，并在确认后再统一应用。
在未确认是“模板升级”前，默认只允许做增量更新，不允许重写模板。

---

## 9. 修改规则

1. 不允许在 service 层重新实现 workflow / hook / trace 主调度
2. 不允许手写 scope 主流程顺序，必须通过 chat_runtime 调用统一 workflow
3. 不允许让 `request_assembler` 之外的模块决定上下文装配顺序
4. 不允许在 service 层直接实现 parser / chunker / embedding / index 细节
5. 不允许在 service 层生成 citation 内容本身（只消费 retrieval 结果）
6. 不允许在每个 delta 上更新 rolling summary / working memory
7. `app/services/` 中承担结构化结果表达职责的 dataclass（如 result/state 类）字段必须补充中文注释，明确字段在编排链路中的语义。
8. 不允许删除仍在使用的 services dataclass 字段中文注释。
9. 不允许按消费者命名新的应用服务文件或类。
10. 不允许在 service 主编排逻辑中再次形成与 `chat_runtime` 平行的双编排路径。

---

## 10. Code Review 清单

1. services 是否仍保持 façade / 应用入口定位？
2. 是否把主执行语义正确下沉到了 `chat_runtime`？
3. `ChatService` / `StreamingChatService` 的职责是否仍清晰？
4. `request_assembler` 是否仍是唯一装配中枢？
5. completed / failed / cancelled 收口是否仍符合 Phase 4 / Phase 5 约束？
6. 是否没有把向量库、embedding 厂商细节或 workflow 细节直接暴露到 service 业务逻辑中？
7. SSE 交付逻辑是否仍留在 service/API 边界，而不是侵入 runtime？
8. 本次文档更新是否遵守了“文档维护规则”？
9. 是否保持了原有布局、排版、标题层级、写法和风格？

---

## 11. 测试要求

至少覆盖：

1. 同步聊天链路正常工作
2. 流式聊天 started / delta / heartbeat / completed 路径稳定
3. cancel / timeout / error 路径行为稳定
4. completed assistant message 才进入标准 memory update
5. failed / cancelled assistant message 不污染后续 request assembly
6. request_assembler 当前装配顺序正确
7. service 调 runtime 的 façade 行为正确
8. SSE event 与原有 contract 保持兼容

---

## 12. 一句话总结

`app/services/` 在当前代码基线中是 chat 主链路的应用入口与交付 façade；本轮升级的目标不是让它继续长成大编排层，而是让它把主执行语义收口给 `app/chat_runtime/`，自己保持清晰、稳定、可测试的入口职责。
