# CODE_REVIEW.md

> 更新日期：2026-04-13

## 1. 文档定位

本文件定义 `vi_ai_core_service` 的项目级 Code Review 标准、全局审查原则、跨模块检查点与当前阶段专项审查要求。

本文件只负责回答以下问题：

- 当前项目 Review 时应该重点检查什么
- 各层有哪些通用边界检查点
- 当前阶段有哪些专项检查点
- 哪些问题改动应直接拒绝
- 哪些改动必须补测试

本文件不负责：

- 仓库级协作规则
- 项目阶段路线图
- 总体架构设计说明
- 模块级局部实现说明
- 你和我之间的交互流程

这些内容分别由：

- `AGENTS.md`
- `PROJECT_PLAN.md`
- `ARCHITECTURE.md`
- 模块 `AGENTS.md`
- `CHAT_HANDOFF.md`

承担。

---

## 2. Review 目标

Code Review 不只是检查“能不能运行”，还要检查：

1. 是否符合分层结构
2. 是否遵守模块边界
3. 是否与总体架构一致
4. 是否可维护、可扩展、可测试
5. 是否真正统一同步与流式两条主链路
6. 是否让代码事实、文档描述与阶段声明保持一致

---

## 3. 全局审查原则

- 先看边界，再看实现
- 先看结构，再看技巧
- 保守对待会扩大耦合的改动
- 可测试性是硬要求
- 代码事实优先于规划表述与文档描述
- 所有新增或修改的 `@dataclass` 字段，必须逐项检查是否补充了中文字段注释，且注释语义与当前代码一致。
- 所有新增或修改的默认配置常量（如 `DEFAULT_*`），必须检查是否补充了中文注释，且涉及 token、chars、seconds、ttl、size、top-k、threshold 等值时是否写明单位或数值语义。
- 未经明确确认，不允许删除既有中文字段注释或默认配置注释；若字段或配置项仍存在但注释被删除，视为不合格改动。

### 当前阶段额外原则
- Review 重点从“各自维护 sync / stream 编排”升级为“是否真正形成统一 chat runtime 骨架”
- 任何改动都不得让 `ChatService` 与 `StreamingChatService` 重新演化为双编排内核
- workflow 必须显式声明，hook 必须显式配置
- workflow 主步骤、lifecycle hook、step hook 必须边界清晰，不能混成同一个数组
- 当前阶段只允许做 chat runtime 骨架，不得借机实现 Tool Calling / Agent Runtime / runtime skill loader
- citations 仍必须来自 retrieval 结果，不得退化为模型自由生成文本

---

## 4. 项目级通用审查问题

每次 review，至少回答：

1. 代码为什么在这个目录？
2. 逻辑属于哪个层？
3. 是否破坏十层边界？
4. 是否出现跨层绕过？
5. 是否需要同步更新文档？
6. 是否需要补测试？

### 当前阶段补充问题
- 是否把 chat 与 stream 的共同业务语义真正收口到了 `app/chat_runtime/`？
- `ChatService` / `StreamingChatService` 是否只保留 façade / 交付职责？
- `DEFAULT_CHAT_WORKFLOW` 是否足够清晰、可追踪、可测试？
- `DEFAULT_CHAT_HOOKS` 与 `DEFAULT_CHAT_STEP_HOOKS` 是否边界明确？
- `ChatRequestAssembler` 是否仍是唯一 request assembly 中枢？
- `/chat` 与 `/chat_stream` 的 contract 是否未回退？

7. 当前改动是在收敛 chat runtime 骨架，还是偷偷扩大到 Tool Calling / Agent Runtime？
8. hook 是否只承担 lifecycle 拦截 / 记录 / 修正，不承担主业务步骤替身？
9. 是否保持了根目录四文档与模块文档各自职责清晰？

---

## 5. 全局边界检查清单

### API 层
- 路由文件与 URL 分组是否按领域命名（chat / knowledge / evaluation / runtime），而不是按 console 消费者命名？
- 是否只做接入、校验、转发、返回
- SSE 序列化是否留在 API 层
- route 是否没有直接消费 provider 原始 chunk 或 vector index
- 当前 `/chat` 与 `/chat_stream` 契约是否仍与 `app/api/schemas/chat.py` 一致
- citation 是否通过稳定 schema 返回，而不是随意拼接

### Services 层
- 是否仍保持 façade / 应用入口定位，而不是重新扩成主编排内核？
- 是否只做 request/response 级适配与交付？
- 是否把共同执行语义下沉到 `chat_runtime`？
- 是否避免在 service 层通过字符串键直接消费 repository 返回的裸 `dict`？

### Chat Runtime 层
- workflow 是否显式定义？
- workflow 主数组中是否只包含主步骤，而不混入 lifecycle hook？
- lifecycle hook 与 step hook 是否通过单独配置收口？
- run_sync 与 run_stream 是否共享同一套业务语义？
- trace 是否统一收口？
- 是否没有提前做 tool runtime / policy center / agent planner？

### Context / Prompt / RAG / Provider
- context 是否只在 completed 时执行标准 memory update
- rag 是否继续负责 retrieval / knowledge block / citation 生成
- provider 是否继续负责 chat/stream canonical 归一化
- `ChatRequestAssembler` 是否仍保持 system -> knowledge -> working memory -> rolling summary -> recent raw -> user 顺序

### Observability
- 是否仍是结构化日志基础设施，而不是业务状态机
- trace 是否只记录事实，不夹带业务推理

### Schema
- `RuntimeTurnRequest` / `RuntimeTurnContext` / `RuntimeTurnResult` 等执行态对象是否仅位于 `chat_runtime` 或共享 schema 合理位置
- API 对外 schema 是否未与 runtime 内部态耦合
- dataclass 字段是否都有中文注释

---

## 6. 文档一致性检查

每次 Review 必查：

1. 根目录 `AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md` 是否仍各司其职？
2. 模块 `AGENTS.md` 是否只写模块级内容？
3. skill 是否只写执行型约束？
4. 是否把未落地能力写成完成态？
5. 是否保持了现有模板风格、标题层级与章节顺序？

---

## 7. 测试要求（强约束）

凡涉及以下改动，必须补测试：

- `chat_runtime` 新增或调整
- `ChatService` / `StreamingChatService` 主链路改动
- request assembly 改动
- streaming 生命周期改动
- hook / trace / workflow 配置改动

至少应有下列测试之一或多项：

- `/chat` 路由测试
- `/chat_stream` 生命周期测试
- cancel / reset 测试
- request assembly 顺序与过滤测试
- provider normalization 与 registry 测试
- retrieval 失败降级测试
- `DEFAULT_CHAT_WORKFLOW` step dispatch 测试
- lifecycle hook 与 step hook 触发测试
- trace 收口测试
- `ChatService` façade 行为测试
- `StreamingChatService` façade + SSE event 兼容性测试

---

## 8. 当前阶段专项审查清单

### 8.1 Chat Runtime 模块落位
- `app/chat_runtime/` 是否真正新增并承担统一执行骨架职责？
- 是否没有把执行逻辑继续散落在 services？

### 8.2 Workflow 显式化
- 是否存在 `DEFAULT_CHAT_WORKFLOW`？
- workflow 是否按主业务步骤排序？
- 是否避免把 hook 名称混进主 workflow？

### 8.3 Hook 边界清晰
- 是否存在 `DEFAULT_CHAT_HOOKS`？
- 是否存在 `DEFAULT_CHAT_STEP_HOOKS`？
- hook 是否支持最小 continue / warn / mutate / block 等决策形态？
- hook 是否只做生命周期控制，不承担主执行步骤？

### 8.4 Sync / Stream 共语义
- run_sync 与 run_stream 是否共享同一套主流程语义？
- stream 是否只是交付方式不同，而不是重新定义主业务流程？

### 8.5 Services façade 收敛
- `ChatService` 是否只负责同步入口适配与结果返回？
- `StreamingChatService` 是否只负责流式入口适配与 SSE 交付？
- services 是否不再直接承担 workflow / hook / trace 内核职责？

### 8.6 Request Assembly 与 Citation 不回退
- `ChatRequestAssembler` 是否仍是唯一装配中枢？
- citations 是否仍仅来自 retrieval 结果？
- delta 阶段是否仍不携带 citations？

---

## 9. 常见应拒绝的问题改动

- 为了快直接跨层调用
- 在 API 层堆业务逻辑
- provider 直接输出 SSE
- 在每个 delta 上写入 rolling summary / working memory
- 把 workflow、hook、skill、tool、policy 全部一口气做成大平台
- 把 citation 做成模型随意输出的字符串
- 在核心 repository 查询中长期返回裸 `dict`，并让上层以字符串键方式编排主要业务逻辑
- 为了兼容旧结构继续维持 `ChatService` / `StreamingChatService` 双编排内核
- 把 lifecycle hook 混入主 workflow 数组
- 在 hook 中直接硬编码主业务步骤，替代 workflow dispatch
- 本轮借机实现 Tool Calling / Agent Runtime / Planner / Executor
- 未补测试就提交 chat runtime 主链路改动
- 删除仍在使用的 dataclass 字段中文注释
- 删除仍在使用的默认配置常量中文注释

---

## 10. 一句话总结

`CODE_REVIEW.md` 在当前阶段的职责，是保护 `vi_ai_core_service` 的聊天主链路从“双编排”向“统一 chat runtime 骨架”收敛，并确保这个过程既不破坏现有 sync / stream / context / rag / citation 契约，也不越界提前做成更重的 Tool 或 Agent 平台。
