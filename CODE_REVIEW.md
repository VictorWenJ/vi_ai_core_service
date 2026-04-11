# CODE_REVIEW.md

> 更新日期：2026-04-10

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
5. 是否破坏同步与流式两条主链路
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

- 当前已落地主链路仍是 Phase 2~5，不得被“计划中的 Phase 6”改坏
- 若改动声称落地 retrieval / citation，必须同时给出真实代码与测试依据
- 未落地能力不得继续在模块文档、skill、测试矩阵中写成完成态
- 引入知识能力时，不得混淆 short-term memory 与 external knowledge

---

## 4. 项目级通用审查问题

每次 review，至少回答：

1. 代码为什么在这个目录？
2. 逻辑属于哪个层？
3. 是否破坏八层边界？
4. 是否出现跨层绕过？
5. 是否需要同步更新文档？
6. 是否需要补测试？

### 当前阶段补充问题

7. 当前改动是在维护已落地的 Phase 2~5，还是在真实新增 Phase 6 代码？
8. 若涉及 retrieval、citation、chunking、embedding，是否真的有对应代码落位在正确模块？
9. 是否保持了根目录四文档与模块文档各自职责清晰？

---

## 5. 全局边界检查清单

### API 层
- 是否只做接入、校验、转发、返回
- SSE 序列化是否留在 API 层
- route 是否没有直接消费 provider 原始 chunk 或 vector index
- 当前 `/chat` 与 `/chat_stream` 契约是否仍与 `app/api/schemas/chat.py` 一致
- citation 是否通过稳定 schema 返回，而不是随意拼接

### Services 层
- 是否仍然是编排层
- 生命周期状态机、取消协调、完成态收口是否由 services 统一调度
- 当前 request assembly 顺序是否仍为 system -> knowledge -> working memory -> rolling summary -> recent raw -> user
- retrieval 是否由 services 编排，而不是散落到 api/provider/context

### Context / Prompt / RAG / Provider
- 四个专项能力模块是否职责分离
- context 是否只在 completed 时执行标准 memory update
- rag 是否保持“内部子域 + 运行时代码实现”且不越界
- provider 是否保持 chat/stream canonical 归一化与独立 embedding 抽象边界

### Observability
- 是否仍是结构化日志基础设施，而不是业务状态机
- `log_report` 与 JSON-safe 序列化是否仍只记录事实，不夹带业务推理

### Schema
- 是否仍是契约层
- `app/schemas/` 是否仍只承载内部 `LLM*` 契约
- `app/api/schemas/` 是否继续承载对外 request / response / stream event 契约

---

## 6. 全局契约审查标准

必须检查：

- `/chat` 与 `/chat_stream` 输入语义是否尽量一致
- `request_id` / `assistant_message_id` / `finish_reason` / `usage` / `latency` / `error_code` 语义是否统一
- Qdrant、embedding model、collection 之类内部实现细节是否未无意义暴露到外部协议

### 当前阶段补充要求

- 当前 `/chat` 与 `/chat_stream` citation 字段是否与 schema 一致
- citations 为空时行为是否明确（空数组）
- delta 阶段是否没有混入 citation 增量

---

## 7. 全局错误处理审查标准

必须检查：

- client disconnect 是否与 explicit cancel 区分
- provider timeout 与 request timeout 是否区分
- `response.error` 与 `response.cancelled` 是否不混淆
- failed / cancelled assistant message 是否没有进入标准 memory update
- retrieval / embedding / index 失败时是否可降级或可显式失败，而不是静默污染结果

### 当前阶段补充要求

- 当前流式取消、失败、完成路径是否仍各自收口清晰
- 当前同步链路 provider/config 错误是否仍映射稳定
- 若未来新增 Phase 6，ingest / retrieval 失败是否不会拖垮在线 chat 主链路

---

## 8. 全局测试审查标准

以下改动原则上必须补测试：

- 主链路改动
- Provider 行为改动
- Context 行为改动
- Schema 契约改动
- 流式事件顺序、生命周期、取消与失败路径改动
- retrieval、citation、ingest、chunking、embedding、index 改动

### 当前阶段补充要求

至少应有下列测试之一或多项：

- `/chat` 路由测试
- `/chat_stream` 生命周期测试
- cancel / reset 测试
- context manager / store / policy 测试
- request assembly 顺序与过滤测试
- provider normalization 与 registry 测试

- parser / chunker / embedding / index / retrieval 测试
- citation 格式化测试
- `/chat` citation 输出测试
- `/chat_stream` completed citation 输出测试
- retrieval 失败降级测试

---

## 9. 当前阶段专项审查清单

### 9.1 RAG 边界
- `app/rag/` 是否保持为内部子域，而不是无计划扩展成新平台
- 当前代码是否如实反映已落地的 `models / ingestion / retrieval / citation / runtime`
- 若开始新增 RAG 代码，retrieval 是否没有入侵 context 语义
- knowledge retrieval 是否没有替代 working memory / rolling summary

### 9.2 数据与模型
- 当前 `app/schemas/` 中的 `LLMMessage` / `LLMRequest` / `LLMResponse` / `LLMStreamChunk` 是否职责清晰
- API 对外契约是否仍位于 `app/api/schemas/`
- 若开始新增 `KnowledgeDocument` / `KnowledgeChunk` / `RetrievedChunk` / `Citation`，是否职责清晰

### 9.3 Chunking 与 Ingest
- chunking / ingest 实现是否与代码一致
- 是否采用结构感知 + token-aware + overlap
- parser / cleaner / chunker / embedding / index 链路是否清晰

### 9.4 Retrieval 与 Assembly
- request assembly 顺序是否为：
  - system
  - knowledge
  - working memory
  - rolling summary
  - recent raw
  - user
- knowledge block 是否通过统一渲染注入
- citation 是否来自 retrieved chunks，而不是模型自由生成

### 9.5 流式与同步契约
- `/chat` 是否返回 citation 列表且契约稳定
- `/chat_stream` completed 是否返回 citations 且契约稳定
- delta 阶段是否保持轻量且没有额外业务字段漂移

### 9.6 降级与鲁棒性
- 当前流式取消 / 失败 / 完成路径是否仍可运行
- 当前同步 provider / config 错误路径是否稳定
- retrieval 失败时 chat / stream 是否仍可运行
- embedding / index / ingest 异常是否可定位

---

## 10. 常见应拒绝的问题改动

- 为了快直接跨层调用
- 在 API 层堆业务逻辑
- provider 直接输出 SSE
- 在每个 delta 上写入 rolling summary / working memory
- 以 Phase 6 为名偷偷引入长期记忆平台、Agent runtime、审批流或 Case Workspace
- 把 citation 做成模型随意输出的字符串
- 继续使用按字符硬切分作为正式 chunking 主策略
- 在没有抽象边界的前提下直接把 Qdrant/embedding 细节写死进业务层
- 把尚未落地能力写进文档、skill 或测试完成态

### 当前阶段补充拒绝项

- 将 retrieval 结果直接当成 short-term memory 使用
- 在 service 层散落直接访问向量库 SDK 的实现
- 在 API 层直接组织 retrieval 或 citation 业务逻辑
- 在 delta 阶段输出 citation 增量
- 未补测试就提交 Phase 6 相关主链路改动
- 删除仍在使用的 dataclass 字段中文注释
- 删除仍在使用的默认配置常量中文注释
- 新增 dataclass 字段但未补中文字段说明
- 新增或修改默认配置常量但未补中文说明或未标明单位语义
- 将既有中文注释替换为英文、缩写说明或无实际语义的信息性占位文本

---

## 11. 一句话总结

`CODE_REVIEW.md` 在当前阶段的职责，是作为项目级审查标准文件，明确 `vi_ai_core_service` 在当前代码基线下的通用 review 原则、跨模块检查点、专项审查清单与应拒绝改动类型，既保护已落地的 Phase 2~5 主链路，也约束未来 Phase 6 实现必须以真实代码与测试为准。
