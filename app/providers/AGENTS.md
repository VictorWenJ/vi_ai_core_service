# app/providers/AGENTS.md

> 更新日期：2026-04-10

## 1. 文档定位

本文件定义 `app/providers/` 的职责、边界、结构约束与 review 标准。  
当前阶段，本文件临时同时承担该模块的 AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW 职责。
执行 prompts 相关任务时，必须先读根目录`AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md`，再读本文件，再根据skill `skills/python-prompts-capability/`执行。

---

## 2. 模块定位

`app/providers/` 是模型与厂商接入层。  
它负责对接不同大模型厂商，输出统一的 chat completion / stream chunk / embedding 结果，不承担业务编排职责。

当前阶段建议围绕以下职责组织：

- 非流式 chat completion provider
- 流式 chat completion provider
- canonical provider response / canonical stream chunk
- embedding provider 抽象与实现

---

## 3. 本层职责

1. 对接不同厂商的聊天能力
2. 对接不同厂商的流式能力
3. 输出统一的非流式结果结构
4. 输出统一的流式 chunk 结构
5. 在 Phase 6 中提供文本 embedding 抽象与实现
6. 管理 provider 级错误映射与配置

---

## 4. 本层不负责什么

1. 不负责同步或流式 chat 主链路编排
2. 不负责 context state 管理
3. 不负责 retrieval orchestration
4. 不负责 parser / chunker / vector index
5. 不负责 citations 生成
6. 不负责 knowledge block 装配
7. 不负责 request assembly 顺序

---

## 5. 依赖边界

### 允许依赖
- `app/schemas/`（如需要共享基础契约）
- `app/observability/`

### 禁止依赖
- `app/api/`
- `app/services/`
- `app/context/`
- `app/rag/`（除非仅被上层调用，不应形成反向依赖）
- 向量库 SDK

---

## 6. 架构原则

### 6.1 provider 只输出能力，不决定业务
providers 只负责“怎么调用厂商”，不负责“何时调用、怎么编排”。

### 6.2 chat 与 embedding 都应通过抽象暴露
Phase 6 后，不仅 chat provider 要抽象，embedding provider 也必须抽象。

### 6.3 canonical contract 优先
无论不同厂商返回什么结构，provider 层都必须向上层暴露稳定的统一结构。

### 6.4 provider 不关心 citations
provider 只负责生成与 embedding，不负责 retrieval、citation 或外部知识增强逻辑。

---

## 7. 当前阶段能力声明

当前本轮必须保持稳定：

- 非流式 chat completion
- 流式 chat completion
- stream chunk 归一化
- finish / usage / error 归一化

当前本轮新增要求：

- embedding provider 抽象
- 至少一个文本 embedding 基线实现
- embedding 返回结果维度、数据类型、错误映射稳定可测

当前本轮不要求：

- 多模态 embedding 主链路
- 图像 / 音频 / 视频 embedding 主链路
- provider 层直接参与 retrieval

---

## 8. 修改规则

1. 不允许在 provider 层直接访问向量库
2. 不允许在 provider 层直接组织 retrieval query
3. 不允许在 provider 层生成 citations
4. 不允许让厂商原始 embedding 响应直接泄漏给 service / rag
5. 不允许把 retrieval 逻辑混进 chat provider 或 embedding provider

---

## 9. Code Review 清单

1. providers 是否仍然保持为“厂商接入层”？
2. chat 与 embedding 是否都通过抽象暴露？
3. 是否没有将 retrieval / context / citation 逻辑写进 provider 层？
4. embedding 维度与返回类型是否稳定？
5. 错误映射是否合理？
6. 是否没有把底层厂商响应结构直接泄漏给上层？

---

## 10. 测试要求

至少覆盖：

1. embedding provider 基础行为
2. 维度与数据类型稳定性
3. batch 行为（如实现）
4. timeout / error 映射
5. config 加载
6. 不同 provider 的 canonical contract 稳定性

---

## 11. 一句话总结

`app/providers/` 在 Phase 6 中新增文本 embedding 能力，但仍然只承担厂商接入与 canonical contract 输出职责，不参与 retrieval、citation 与 knowledge block 装配。