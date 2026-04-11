# SKILL.md

> skill_name: python-service-capability
> module_scope: app/services/
> status: active
> last_updated: 2026-04-10

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `app/services/` 模块中进行应用编排层的设计、实现、测试与增量演进。

本 skill 的目标不是生成“泛化的 chat service 示例”，而是约束在本项目文档治理体系下，按当前仓库真实代码结构实现：

- 同步 chat 编排
- 流式 chat 编排
- request assembly
- cancellation registry
- assistant message lifecycle 收口
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
7. 长期记忆平台
8. Agent Runtime
9. 审批流
10. Case Workspace

如任务超出上述边界，应转交对应模块 skill 处理。

---

## 4. 本 skill 的核心原则

### 4.1 services 是编排层
services 负责“何时调用谁、如何收口”，不负责底层存储、SDK 调用与协议输出。

### 4.2 request_assembler 是唯一装配中枢
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

### 4.4 流式生命周期必须收敛在 services
`started / delta / heartbeat / completed / error / cancelled` 的业务语义由 services 统一调度。

### 4.5 当前代码已落地 RAG 编排
当前仓库中的 services 已有 retrieval、knowledge block、citations 运行时编排逻辑。
后续迭代必须继续在本层统一编排，不能散落到 API / provider / context。

### 4.6 同步入口收敛
同步聊天正式入口以 `chat_with_citations_from_user_prompt` 为准。
不得为了历史测试长期保留旧同步入口双轨兼容。

---

## 5. 默认阶段基线

当前 skill 默认基线如下：

- `ChatService` 负责编排同步 chat
- `StreamingChatService` 负责编排流式 chat
- `ChatRequestAssembler` 负责上下文组装与请求规范化
- `CancellationRegistry` 负责请求级取消
- `PromptService` 负责消息装配辅助
- 当前代码包含 retrieval / citation 编排

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

1. 同步 chat 编排更新
2. 流式 chat 编排更新
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

### 8.2 流式链路约束
流式链路必须继续保持：

- request_id / assistant_message_id 生成稳定
- placeholder / delta / finalize 收口稳定
- cancel / timeout / error 路径稳定

### 8.3 装配约束
`request_assembler` 之外的模块不得决定上下文装配顺序。

### 8.4 依赖约束
services 可依赖：

- `app/context/`
- `app/prompts/`
- `app/providers/`
- `app/schemas/`
- `app/api/schemas/` 的用户请求模型
- `app/observability/`

不得直接散落访问 Redis client、向量库 SDK 或 provider 原始 SDK。

### 8.5 Phase 6 约束
当前代码已落地 retrieval / citations。
新增这类能力的改动，必须同时补真实代码与测试。

### 8.6 历史兼容清理约束
当确认旧接口仅用于历史测试兼容时，应在 services 层移除对应分支，并同步更新测试到当前正式接口。

### 8.7 中文字段注释与默认配置说明约束

1. 本模块中所有 `@dataclass` 定义的结构化对象，必须为每一个字段补充中文注释，说明字段含义。
2. 本模块中所有默认配置常量、默认阈值或默认限制项，必须补充中文注释；涉及 token、chars、seconds、ttl、size、top-k、threshold 等值时，必须明确单位或语义。
3. 上述中文注释属于交付物的一部分。除非字段或常量被明确删除，否则后续改动不得删除、不得改为英文、不得在重构中丢失。
4. 字段或配置项语义变化时，必须同步更新对应中文注释。

---

## 9. 与其他模块的协作约束

### 与 api 协作
API 负责协议接入与 SSE 序列化；services 负责编排。
services 不接管 route handler 职责。

### 与 context 协作
context 负责状态与 memory update；services 负责何时更新、何时收口。

### 与 prompts 协作
prompts 负责模板资产；services 负责决定何时取默认 system prompt 并组装消息。

### 与 providers 协作
providers 负责厂商适配与 canonical result；services 负责调用时机与结果收口。

### 与 rag 协作
当前代码已接入 rag。
rag 负责知识实现，services 负责编排。

---

## 10. 测试要求

service 相关实现至少补以下测试之一或多项：

1. 同步 chat 基础路径
2. 流式 chat 生命周期路径
3. cancel / timeout / error 路径
4. request assembly 顺序与过滤路径
5. completed 才进入标准 memory update 路径
6. 默认 provider / model / system prompt 解析路径
7. retrieval degrade 不拖垮 chat/stream 主链路

---

## 11. Review 要点

提交前至少自查：

1. services 是否仍然只是编排层？
2. request_assembler 是否仍是唯一装配中枢？
3. completed / failed / cancelled 语义是否仍清晰？
4. 是否没有把 route / SDK / store 细节混入 services？
5. retrieval / citations 是否仍保持 services 编排边界？
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

本 skill 的目标，是确保 `app/services/` 在当前项目中持续作为应用编排层演进，稳定承接同步 / 流式 chat、request assembly、retrieval 编排与生命周期收口。
