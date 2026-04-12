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
- Review 重点从“评估与离线构建基础”升级为“控制面正式持久化是否正确落地”
- 任何改动都不得让 `RAGControlState` 以正式状态容器形式回流
- 控制面 API 与服务命名必须按领域职责收敛，不按当前消费者命名。
- `app/api/` 中正式路由文件不得继续使用 `*_console.py` 作为长期命名。
- `app/rag/` 中不得继续维持消费者导向的聚合型 `console_service` 作为长期结构。
- 文档加载器允许引入成熟框架，但 loader 框架只能位于输入适配层，不得接管内部 RAG 主链路。

- 当前已落地主链路覆盖 Phase 2~6，不得被不受控改动破坏
- Phase 7 只能增强评估与离线构建基础，不得借机改坏在线 chat / stream / context / citation 契约
- 若改动声称新增 benchmark、构建批次、版本元数据或质量门禁，必须同时给出真实代码、测试与结果依据
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
- 文档、版本、构建任务、chunk、evaluation run / case 是否已正式落盘？
- 是否出现内存状态与 MySQL 并存的双真相源？
- 是否在 `chunks` 表中错误冗余存储完整向量值？
- 是否把 SQL 散落进 API / service，而不是收敛到 `repository`？

7. 当前改动是在维护已落地的 Phase 2~6，还是在真实新增 Phase 7 评估 / 构建能力？
8. 若涉及 retrieval、citation、chunking、embedding、benchmark、build 元数据，是否真的有对应代码落位在正确模块？
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
- 是否仍保持按应用职责拆分，而不是把控制面能力塞进消费者导向的 God Service？
- 是否仍然是编排层
- 生命周期状态机、取消协调、完成态收口是否由 services 统一调度
- 当前 request assembly 顺序是否仍为 system -> knowledge -> working memory -> rolling summary -> recent raw -> user
- retrieval 是否由 services 编排，而不是散落到 api/provider/context

### Context / Prompt / RAG / Provider
- loader 框架的引入是否仅停留在 ingest 输入适配层，而没有污染内部 chunk / retrieval / citation / build 语义？
- 四个专项能力模块是否职责分离
- context 是否只在 completed 时执行标准 memory update
- rag 是否保持“内部子域 + 运行时代码实现”且不越界
- provider 是否保持 chat/stream canonical 归一化与独立 embedding 抽象边界

### Observability
- 是否仍是结构化日志基础设施，而不是业务状态机
- `log_report` 与 JSON-safe 序列化是否仍只记录事实，不夹带业务推理

### Schema
- `app/api/schemas/` 是否仍只承载对外 request / response contract？
- 领域内部模型是否仍留在各自模块内？
- 是否仍是契约层
- `app/schemas/` 是否仍只承载内部 `LLM*` 契约
- `app/api/schemas/` 是否继续承载对外 request / response / stream event 契约

---

## 6. 全局契约审查标准

必须检查：

- Pydantic / dataclass / schema 是否表达清晰、边界明确
- API contract 是否没有泄漏内部实现细节
- 字段命名是否语义稳定、可演进
- 流式与非流式契约是否一致且可预期

### 当前阶段补充要求
- API 契约变更是否保持最小必要原则？
- 新增字段是否遵守 `*_details` / `*_ids` 命名规则？
- `app/api/schemas/` 是否仍仅承载对外 request / response contract？
- 领域内部模型是否没有被粗暴搬入 `app/schemas/`？
- `/chat` 与 `/chat_stream` citations 字段是否与 schema 一致且完成态输出位置不变？

---


## 7. 全局错误处理审查标准

必须检查：

- client disconnect 是否与 explicit cancel 区分
- provider timeout 与 request timeout 是否区分
- `response.error` 与 `response.cancelled` 是否不混淆
- failed / cancelled assistant message 是否没有进入标准 memory update
- retrieval / embedding / index 失败时是否可降级或可显式失败，而不是静默污染结果

### 当前阶段补充要求
- build / evaluation 失败是否明确落为任务失败状态，而不是静默停留在中间态？
- 当前流式取消、失败、完成路径是否仍各自收口清晰？
- 当前同步链路 provider/config 错误是否仍映射稳定？
- 控制面迁移后，knowledge / runtime 查询失败是否不会误报为 chat 主链路失败？

---


## 8. 全局测试审查标准

以下改动原则上必须补测试：

- 主链路改动
- Provider 行为改动
- Context 行为改动
- Schema 契约改动
- 流式事件顺序、生命周期、取消与失败路径改动
- retrieval、citation、ingest、chunking、embedding、index、benchmark、offline build 改动
- 持久化控制面与 repository / content_store 改动

### 当前阶段补充要求
- 是否新增了 document upload -> persistence -> build -> inspector 的回归测试？
- 是否新增了 evaluation run / case 全量持久化测试？
- 是否新增了服务重启后仍可查询控制面的测试？

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
- document / document_version 持久化测试
- build_task / build_documents / chunks 持久化测试
- evaluation_runs / evaluation_cases 持久化测试
- Inspector 按 `vector_point_id` 回读向量详情测试

---


## 9. 当前阶段专项审查清单

### 9.1 RAG 控制面迁移
- `RAGControlState` 是否已退出正式控制面角色？
- `app/api/deps.py` 是否已改为装配 repository / content_store / vector store，而不是装配 state？
- 是否避免了内存与 MySQL 双写双读？

### 9.2 MySQL 控制面与内容存储分层
- `documents`、`document_versions`、`build_tasks`、`build_documents`、`chunks`、`evaluation_runs`、`evaluation_cases` 是否职责清晰？
- 原始文件与 normalized text 是否落到内容存储，而不是粗暴塞进 MySQL 控制面表？
- hash、parser / cleaner 名称、manifest 输入快照等追溯信息是否保留？

### 9.3 Chunking 与向量边界
- `chunks` 是否只保存元数据、`vector_point_id`、向量维度与 collection，而不是完整向量值？
- 查看向量详情是否通过 Inspector 按 `vector_point_id` 回读 Qdrant？
- Qdrant 是否仍是唯一正式向量检索数据面？

### 9.4 Build Task 语义
- `build_tasks` 是否按任务对象建模？
- `manifest_details` 是否表达“本次 build 输入快照”？
- `build_documents` 是否能回答“本次任务处理了哪些文档版本、结果如何”？

### 9.5 Evaluation 全量持久化
- `evaluation_runs` 与 `evaluation_cases` 是否全量落盘？
- run 是否与 `build_id` 绑定？
- case 级 retrieval / citation / answer 结果是否可回放？

### 9.6 API / Console 契约稳定性
- 后端持久化升级是否尽量不破坏现有领域 API 路径？
- Internal Console 若需跟随更新，是否只围绕契约变化做最小增量修改？

### 9.7 可恢复性与最小闭环
- 服务重启后，knowledge / build / evaluation / runtime summary 是否仍可正确查询？
- upload -> build -> inspector -> evaluation 的最小闭环是否完整？

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
- 为了做评估或离线构建，直接把实验脚本逻辑塞进在线 chat / stream 主链路
- 没有 query/label 分层就把 LLM 合成问答直接当正式黄金集

### 当前阶段补充拒绝项
- 把完整向量值冗余写入 `chunks` 主表
- 保留或新增新的进程内正式控制面容器
- 为了“快”在 API / service 中直接写 SQL
- 用 MySQL 替代 Qdrant 的检索职责
- 在未完成控制面持久化前直接引入异步任务系统并把复杂度前置
- 以 `*_console.py` 或 `console_service.py` 形式长期固化消费者导向命名
- 为了前端便利直接把 runtime / build / evaluation / inspector 全塞进单一聚合服务
- 让 LangChain 或其他框架 Document/loader 直接渗透为内部一等领域模型

- 将 retrieval 结果直接当成 short-term memory 使用
- 在 service 层散落直接访问向量库 SDK 的实现
- 在 API 层直接组织 retrieval 或 citation 业务逻辑
- 在 delta 阶段输出 citation 增量
- 未补测试就提交 Phase 6 相关主链路改动
- 为了让旧测试继续通过而保留历史方法名兼容分支
- 保留仅覆盖旧 contract 的过时 fake/stub/mock 与测试用例
- 删除仍在使用的 dataclass 字段中文注释
- 删除仍在使用的默认配置常量中文注释
- 新增 dataclass 字段但未补中文字段说明
- 新增或修改默认配置常量但未补中文说明或未标明单位语义
- 将既有中文注释替换为英文、缩写说明或无实际语义的信息性占位文本

---

## 11. 一句话总结

`CODE_REVIEW.md` 在当前阶段的职责，是作为项目级审查标准文件，明确 `vi_ai_core_service` 在当前代码基线下的通用 review 原则、跨模块检查点、专项审查清单与应拒绝改动类型，既保护已落地的 Phase 2~7 主链路，也约束当前控制面持久化升级必须以真实代码、真实契约与真实测试为准。
