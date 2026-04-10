# app/observability/AGENTS.md

> 更新日期：2026-04-10

## 1. 文档定位

本文件定义 `app/observability/` 的职责、边界、结构约束、开发约束与 review 标准。  
当前阶段，本文件临时同时承担该模块的 `AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW` 职责。  
执行 observability 相关任务时，必须先读根目录 `AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md`，再读本文件，再根据 skill `skills/python-observability-capability/` 执行。

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

`app/observability/` 是系统的可观测性基础设施层。  
它负责为同步聊天、流式聊天、上下文工程、知识检索与后续能力演进提供统一的结构化日志与调试支撑能力。

当前阶段建议围绕以下职责组织：

- 结构化日志输出
- JSON-safe 序列化
- request / stream / retrieval 相关 trace 字段组织
- 观测辅助工具函数
- 与主链路协作的事实型记录能力

---

## 3. 本模块职责

1. 提供统一的结构化日志能力
2. 提供 JSON-safe 的日志字段序列化能力
3. 为同步 chat 提供可观测性支撑
4. 为流式 chat 提供可观测性支撑
5. 为 context lifecycle 提供可观测性支撑
6. 在 Phase 6 中为 retrieval / citation 提供可观测性支撑
7. 为问题排查、回归验证、联调调试提供事实型记录能力

---

## 4. 本模块不负责什么

1. 不负责 chat 主链路编排
2. 不负责 assistant message lifecycle 状态机推进
3. 不负责 request assembly
4. 不负责 retrieval query 构建
5. 不负责 citation 生成
6. 不负责 context state 更新
7. 不负责 provider 或向量库调用

---

## 5. 依赖边界

### 允许依赖
- 标准库
- 项目内基础 schema / utility（如当前仓库已有）

### 禁止依赖
- 反向依赖业务层状态机
- 把 observability 写成另一个 services 层
- 在 observability 内直接访问 provider / context / rag 的底层资源

### 原则
`app/observability/` 只做基础设施支撑，不做业务决策。

---

## 6. 架构原则

### 6.1 结构化优先
所有日志必须尽量保持结构化、JSON-safe、可检索。

### 6.2 只记录事实，不记录业务推理
observability 记录：
- request_id
- session_id
- conversation_id
- assistant_message_id
- provider / model
- status / finish_reason / error_code
- retrieval_query
- retrieved_chunk_count
- citation_count

不记录：
- 随意业务解释
- 不必要的大段正文
- 不可控敏感内容

### 6.3 不能因为日志破坏主链路
不可序列化对象不能直接进入日志。  
新增 retrieval / citation 可观测性时，必须继续遵守 JSON-safe 原则。

### 6.4 retrieval 观测是 Phase 6 新重点
需要能定位：
- 是否启用了 retrieval
- 为什么没召回
- 为什么 citation 为空
- retrieval 使用了什么 filter / top-k
- 使用了什么 embedding model / index backend

### 6.5 observability 是横切支撑，不反向驱动业务
日志帮助定位问题，但不能决定：
- 是否检索
- 是否取消
- 是否进入 memory update
- 是否输出 citation

---

## 7. 当前阶段能力声明

当前本轮必须保持稳定：

- 同步 chat 可观测性
- 流式 chat 可观测性
- started / delta / completed / cancelled / error 相关观测
- lifecycle 与 cancel registry 相关观测

当前本轮新增要求：

- retrieval_query
- retrieval_top_k
- retrieval_filters
- retrieved_chunk_count
- retrieved_document_ids
- citation_count
- embedding_model
- vector_index_backend

当前本轮不要求：

- 完整 tracing 平台
- metrics 平台
- 告警系统
- 统一监控后台

---

## 8. 文档维护规则（强约束）

本文件属于 `app/observability/` 模块的治理模板资产。  
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
如果未来需要升级 `app/observability/AGENTS.md` 的模板，必须先明确说明这是一次“模板升级”，并在确认后再统一应用。  
在未确认是“模板升级”前，默认只允许做增量更新，不允许重写模板。

---

## 9. 修改规则

1. 不允许把不可 JSON-safe 的对象直接打进日志
2. 不允许在 observability 层实现 chat / stream / retrieval 业务逻辑
3. 不允许输出过量 chunk 原文正文或敏感内容
4. 不允许 retrieval / citation 相关字段命名混乱、无统一约定
5. 不允许用日志替代正式状态存储

---

## 10. Code Review 清单

1. observability 是否仍然是基础设施层，而不是业务编排层？
2. 同步与流式链路的关键字段是否可观测？
3. retrieval / citation 相关字段是否齐全且命名稳定？
4. 是否保证日志 JSON-safe？
5. 是否没有把大段原始知识文本、敏感数据无控制地写入日志？
6. 新增可观测性是否没有破坏流式主链路？
7. 本次文档更新是否遵守了“文档维护规则”？
8. 是否保持了原有布局、排版、标题层级、写法和风格？

---

## 11. 测试要求

至少覆盖：

1. JSON-safe 序列化
2. request / stream 相关 trace 字段输出
3. retrieval trace 字段输出
4. citation_count 等字段输出
5. 流式场景下 observability 不因不可序列化对象崩溃

---

## 12. 一句话总结

`app/observability/` 在当前阶段是系统的结构化观测基础设施层，为同步聊天、流式聊天、上下文生命周期与 Phase 6 的 retrieval / citation 提供事实型、JSON-safe、可回归的可观测性支撑，而不参与业务编排与状态决策，并在后续更新中严格遵守模块文档的模板冻结规则。