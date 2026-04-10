# app/observability/AGENTS.md

> 更新日期：2026-04-10

## 1. 文档定位

本文件定义 `app/observability/` 的职责、边界、结构约束与 review 标准。  
当前阶段，本文件临时同时承担该模块的 AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW 职责。
执行 observability 相关任务时，必须先读根目录`AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md`，再读本文件，再根据skill `skills/python-observability-capability/`执行。

---

## 2. 模块定位

`app/observability/` 是系统的可观测性基础设施层。  
它负责结构化日志、调试辅助与运行时可观测性支撑，不负责业务编排和状态机推进。

---

## 3. 本层职责

1. 提供 JSON-safe 的结构化日志能力
2. 为同步 chat 提供可观测性支撑
3. 为流式 chat 提供可观测性支撑
4. 为 assistant message lifecycle 提供可观测性支撑
5. 在 Phase 6 中为 retrieval / citation 提供可观测性支撑

---

## 4. 本层不负责什么

1. 不负责 chat 主链路编排
2. 不负责 request assembly
3. 不负责 retrieval query 构建
4. 不负责 citations 生成
5. 不负责 context state 更新
6. 不负责 provider 或向量库调用

---

## 5. 依赖边界

### 允许依赖
- 标准库
- 项目内基础 schema / utility（如当前仓库已有）

### 禁止依赖
- 反向依赖业务层状态机
- 把 observability 写成另一个 services 层

---

## 6. 架构原则

### 6.1 结构化优先
所有日志必须尽量保持结构化、JSON-safe、可检索。

### 6.2 只记录事实，不记录业务推理
observability 记录：
- request_id
- conversation_id
- status
- provider/model
- retrieval_query
- retrieved_chunk_count
- citation_count

不记录：
- 随意业务解释
- 不必要的大段正文
- 不可控敏感内容

### 6.3 不能因为日志破坏主链路
上一阶段已经验证过：不可序列化对象不能直接进入日志。  
Phase 6 新增 retrieval / citation 可观测性时，必须继续遵守 JSON-safe 原则。

### 6.4 retrieval 观测是新增重点
需要能定位：
- 为什么没召回
- 为什么召回数量异常
- 为什么 citations 为空
- retrieval 是否启用
- 使用了什么 filter / top-k

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

---

## 8. 修改规则

1. 不允许把不可 JSON-safe 的对象直接打进日志
2. 不允许在 observability 层实现 retrieval 或 citation 业务逻辑
3. 不允许输出过量 chunk 原文正文
4. 不允许 retrieval 相关字段命名混乱、无统一约定

---

## 9. Code Review 清单

1. observability 是否仍然是基础设施层，而不是业务编排层？
2. retrieval / citation 相关字段是否齐全且命名稳定？
3. 是否保证日志 JSON-safe？
4. 是否没有把大段原始知识文本、敏感数据无控制地写入日志？
5. 新增可观测性是否没有破坏流式主链路？

---

## 10. 测试要求

至少覆盖：

1. JSON-safe 序列化
2. retrieval trace 字段输出
3. citation_count 等字段输出
4. 流式场景下 observability 不因不可序列化对象崩溃

---

## 11. 一句话总结

`app/observability/` 在 Phase 6 中新增 retrieval / citation 的结构化观测，但仍然只做事实记录与调试支撑，不参与业务会话编排与知识检索实现。