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
6. 是否以可追溯引用的方式接入知识能力

---

## 3. 全局审查原则

- 先看边界，再看实现
- 先看结构，再看技巧
- 保守对待会扩大耦合的改动
- 可测试性是硬要求
- citation 与知识时效性是 Phase 6 的核心审查对象

### 当前阶段额外原则

- retrieval 是增强层，不得破坏 chat 主链路
- citation 必须来自 retrieval 结果，不得变成模型自由生成文本
- chunking 必须从“按字符切分”升级到结构感知 + token-aware + overlap
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

7. 当前改动是否仍属于 Phase 6 边界？
8. 是否把 retrieval、citation、chunking、embedding 等内容放在了正确模块？
9. 是否保持了根目录四文档与模块文档各自职责清晰？

---

## 5. 全局边界检查清单

### API 层
- 是否只做接入、校验、转发、返回
- SSE 序列化是否留在 API 层
- route 是否没有直接消费 provider 原始 chunk 或 vector index
- citation 是否通过稳定 schema 返回，而不是随意拼接

### Services 层
- 是否仍然是编排层
- 生命周期状态机、取消协调、完成态收口是否由 services 统一调度
- retrieval 是否由 services 编排，而不是散落到 api/provider/context

### Context / Prompt / RAG / Provider
- 四个专项能力模块是否职责分离
- context 是否只在 completed 时执行标准 memory update
- rag 是否只负责 ingest / retrieval / citation 相关实现
- provider 是否只做 canonical response / stream chunk / embedding 归一化

### Observability
- 是否仍是结构化日志基础设施，而不是业务状态机
- retrieval trace 是否只记录事实，不夹带业务推理

### Schema
- 是否仍是契约层
- citation / stream event / lifecycle / cancel contract 是否清晰稳定

---

## 6. 全局契约审查标准

必须检查：

- `/chat` 与 `/chat_stream` 输入语义是否尽量一致
- `/chat` 是否返回 citations
- `/chat_stream` 是否仅在完成事件返回 citations
- `request_id` / `assistant_message_id` / `finish_reason` / `usage` / `latency` / `error_code` / `citations` 语义是否统一
- Qdrant、embedding model、collection 之类内部实现细节是否未无意义暴露到外部协议

### 当前阶段补充要求

- citations 是否为空时行为明确
- delta 阶段是否没有混入 citation 增量
- retrieval 结果是否没有以内部对象全量透传给外部响应

---

## 7. 全局错误处理审查标准

必须检查：

- client disconnect 是否与 explicit cancel 区分
- provider timeout 与 request timeout 是否区分
- `response.error` 与 `response.cancelled` 是否不混淆
- failed / cancelled assistant message 是否没有进入标准 memory update
- retrieval / embedding / index 失败时是否可降级或可显式失败，而不是静默污染结果

### 当前阶段补充要求

- retrieval 失败时 `/chat` 是否仍可运行
- retrieval 失败时 `/chat_stream` 是否仍保持正确收口
- ingest 失败是否不会拖垮在线 chat 主链路

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

- parser 测试
- chunker 测试
- embedding provider 测试
- index upsert / query 测试
- retrieval service 测试
- citation 格式化测试
- `/chat` citation 输出测试
- `/chat_stream` completed citation 输出测试
- retrieval 失败降级测试

---

## 9. 当前阶段专项审查清单

### 9.1 RAG 边界
- `app/rag/` 是否保持为内部子域，而不是无计划扩展成新平台
- retrieval 是否没有入侵 context 语义
- knowledge retrieval 是否没有替代 working memory / rolling summary

### 9.2 数据与模型
- `KnowledgeDocument` / `KnowledgeChunk` / `RetrievedChunk` / `Citation` 等模型是否职责清晰
- metadata 是否足够支撑 citation、过滤与时效性展示
- 向量维度、distance metric、embedding model 是否一致

### 9.3 Chunking 与 Ingest
- 是否已从“按字符切分”升级为结构感知 + token-aware + overlap
- chunking 是否稳定、可测试、可解释
- parser / chunker / embedding / index 是否链路清晰

### 9.4 Retrieval 与 Assembly
- request assembly 顺序是否为：
  - system
  - working memory
  - rolling summary
  - retrieved knowledge
  - recent raw
  - user
- retrieval 结果是否通过统一 knowledge block 渲染
- citation 是否来自 retrieved chunks，而不是模型自由生成

### 9.5 流式与同步契约
- `/chat` 是否返回 citation 列表
- `/chat_stream` 是否仅在完成事件返回 citations
- delta 阶段是否没有混入 citation 增量

### 9.6 降级与鲁棒性
- retrieval 失败时 chat 是否仍可运行
- 无召回时是否行为稳定
- embedding / index 异常是否可定位
- ingest 失败是否不会影响在线 chat

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

### 当前阶段补充拒绝项

- 将 retrieval 结果直接当成 short-term memory 使用
- 在 service 层散落直接访问向量库 SDK 的实现
- 在 API 层直接组织 retrieval 或 citation 业务逻辑
- 在 delta 阶段输出 citation 增量
- 未补测试就提交 Phase 6 相关主链路改动

---

## 11. 一句话总结

`CODE_REVIEW.md` 在当前阶段的职责，是作为项目级审查标准文件，明确 `vi_ai_core_service` 在 Phase 6 中的通用 review 原则、跨模块检查点、专项审查清单与应拒绝改动类型，确保系统在引入 Knowledge + Citation Layer 时仍保持分层清晰、契约稳定、主链路可回归。