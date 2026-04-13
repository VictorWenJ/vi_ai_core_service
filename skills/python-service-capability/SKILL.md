# SKILL.md

> skill_name: python-service-capability
> module_scope: app/services/
> status: active
> last_updated: 2026-04-13

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `app/services/` 模块中进行应用入口层的设计、实现、测试与增量演进。

本 skill 的目标不是生成“泛化的 chat service 示例”，而是约束在本项目文档治理体系下，按当前仓库真实代码结构实现：

- 同步 chat 入口 façade
- 流式 chat 入口 façade
- runtime request/result 适配
- SSE 交付协作
- cancellation registry 协作
- 与 `app/chat_runtime/` 的稳定协作
- 与 context / prompts / providers 的稳定协作

---

## 2. Skill 适用范围

本 skill 适用于以下类型的工作：

1. `chat_service.py`
2. `streaming_chat_service.py`
3. `request_assembler.py`
4. `cancellation_registry.py`
5. `prompt_service.py`
6. service 级错误收敛
7. service 相关测试

---

## 3. Skill 不适用范围

本 skill 不用于以下工作：

1. HTTP 路由与 SSE 文本协议
2. provider SDK 适配
3. context store 底层实现
4. Prompt 资产注册与模板渲染内部实现
5. retrieval / chunking / embedding / index 运行时代码
6. citation 生成逻辑
7. `app/chat_runtime/` 内部 workflow / hook / trace 主逻辑
8. Tool Calling / Agent Runtime
9. 审批流
10. Case Workspace

如任务超出上述边界，应转交对应模块 skill 处理。

---

## 4. 本 skill 的核心原则

### 4.1 services 是 façade 层
services 负责“接住请求、转给 runtime、交付结果”，不再承担 chat 主执行内核。

### 4.2 request_assembler 仍是唯一装配中枢
当前代码中，装配顺序固定为：

- system prompt
- knowledge block
- working memory block
- rolling summary block
- recent raw messages
- current user input

### 4.3 completed 才进入标准 memory update
- completed：进入标准 update pipeline
- failed / cancelled：只更新消息状态，不进入标准 memory update
- delta：只做传输与聚合，不写 rolling summary / working memory

### 4.4 流式交付留在 services / api 边界
`started / delta / heartbeat / completed / error / cancelled` 的对外交付由 services / api 边界协作完成；其业务语义由 chat runtime 统一定义。

### 4.5 当前代码已落地 RAG 编排
当前仓库中的 retrieval、knowledge block、citations 运行时编排逻辑在收敛后由 chat runtime 统一调度；services 只消费其结果。

### 4.6 同步与流式入口收敛
同步聊天正式入口与流式聊天正式入口都应以 chat runtime 为唯一主执行来源。

### 4.7 当前阶段边界
benchmark runner 可以继续复用正式在线入口，但 services 不承担 workflow / hook / trace 内核。

---

## 5. 默认阶段基线

当前 skill 默认基线如下：

- `ChatService` 负责编排同步 chat 入口 façade
- `StreamingChatService` 负责编排流式 chat 入口 façade
- `ChatRequestAssembler` 负责上下文组装与请求规范化
- `CancellationRegistry` 负责请求级取消
- `app/chat_runtime/` 负责 workflow / hook / trace / invoke 主执行语义
- 当前代码包含 retrieval / citation 编排，但主调度逐步收敛到 chat runtime

如需变更该基线，必须先更新根目录文档与模块 AGENTS，再进入实现。

---

## 6. 标准执行流程

执行 `app/services/` 相关任务时，必须遵循以下顺序：

1. 阅读根目录文档
   - `AGENTS.md`
   - `PROJECT_PLAN.md`
   - `ARCHITECTURE.md`
   - `CODE_REVIEW.md`

2. 阅读模块文档
   - `app/services/AGENTS.md`

3. 阅读本 skill
   - `skills/python-service-capability/SKILL.md`

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

service 相关任务，至少应交付以下之一或多项：

1. 同步 chat façade 更新
2. 流式 chat façade 更新
3. request assembly 更新
4. cancellation registry 更新
5. service 错误收敛更新
6. service 相关测试更新

仅给概念说明、不落代码、不补测试，不视为完成。

---

## 8. 实现约束

### 8.1 同步链路约束
同步链路必须继续保持：

- provider / model 解析稳定
- system prompt 注入稳定
- context completed 收口稳定
- 统一调用 chat runtime

### 8.2 流式链路约束
流式链路必须继续保持：

- request_id / assistant_message_id 生成稳定
- SSE 事件交付稳定
- cancel / timeout / error 路径稳定
- 统一调用 chat runtime

### 8.3 装配约束
`request_assembler` 之外的模块不得决定上下文装配顺序。

### 8.4 依赖约束
services 可依赖：

- `app/chat_runtime/`
- `app/context/`
- `app/prompts/`
- `app/providers/`
- `app/schemas/`
- `app/api/schemas/` 的用户请求模型
- `app/observability/`

不得直接散落访问 Redis client、向量库 SDK 或 provider 原始 SDK。

### 8.5 当前阶段约束
新增这类能力的改动，必须同时补真实代码与测试。

### 8.6 历史兼容清理约束
当确认旧入口或旧服务路径仅用于历史兼容时，应在 services 层移除对应分支，并同步更新测试到当前正式入口。

### 8.7 命名收敛约束
不允许新增按 console、debug、playground 等消费者命名的长期应用服务文件或类。

### 8.8 中文字段注释与默认配置说明约束

1. 本模块中所有 `@dataclass` 定义的结构化对象，必须为每一个字段补充中文注释，说明字段含义。
2. 本模块中所有默认配置常量、默认阈值或默认限制项，必须补充中文注释；涉及 token、chars、seconds、ttl、size、top-k、threshold 等值时，必须明确单位或语义。
3. 上述中文注释属于交付物的一部分。除非字段或常量被明确删除，否则后续改动不得删除、不得改为英文、不得在重构中丢失。
4. 字段或配置项语义变化时，必须同步更新对应中文注释。

---

## 9. 与其他模块的协作约束

### 与 api 协作
API 负责协议接入与 SSE 序列化；services 负责 façade 与交付。
services 不接管 route handler 职责。

### 与 chat_runtime 协作
chat_runtime 负责统一执行骨架；services 负责调用它并交付结果。

### 与 context 协作
context 负责状态与 memory update；services 只协调何时交给 runtime / context 收口。

### 与 prompts 协作
prompts 负责模板资产；services 不重新定义 prompt 资产治理。

### 与 providers 协作
providers 负责厂商适配与 canonical result；services 不直接散落调用厂商 SDK。

### 与 rag 协作
当前代码已接入 rag。
services 不直接承担 retrieval 主调度，只消费收敛后的 runtime 结果。

---

## 10. 测试要求

service 相关实现至少补以下测试之一或多项：

1. 同步 chat façade 路径
2. 流式 chat façade 路径
3. cancel / timeout / error 路径
4. request assembly 顺序与过滤路径
5. façade 调用 runtime 的路径
6. SSE 交付路径
7. retrieval degrade 不拖垮 chat/stream 主链路

---

## 11. Review 要点

提交前至少自查：

1. services 是否仍是 façade 层，而不是双编排内核？
2. `request_assembler` 是否仍是唯一装配中枢？
3. SSE 交付是否仍留在 services / api 边界？
4. 是否没有把 workflow / hook / trace 逻辑重新塞回 services？
5. 是否仍符合模块边界与根文档要求？
