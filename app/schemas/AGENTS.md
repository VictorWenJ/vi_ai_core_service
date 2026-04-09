# app/schemas/AGENTS.md

> 更新日期：2026-04-09

## 1. 文档定位

本文件定义 `app/schemas/` 的职责、边界、结构约束与 review 标准。  
当前阶段，本文件临时同时承担该模块的 AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW 职责。

---

## 2. 模块定位

`app/schemas/` 是系统的数据模型层。  
它负责定义系统内外部交互使用的数据契约，使不同模块之间能以统一、清晰、稳定的方式交换数据。

当前阶段 schema 需要同时承接：

- 同步 chat request / response
- 流式 chat request 扩展
- stream event payload
- cancel request
- message lifecycle 相关状态表示

---

## 3. 本层职责

1. 定义请求模型
2. 定义响应模型
3. 定义 stream event / lifecycle / cancel 相关 contract
4. 作为跨模块的数据契约载体
5. 提供字段层面的语义稳定性

---

## 4. 本层不负责什么

1. 不负责业务流程编排
2. 不负责 HTTP 路由
3. 不负责 provider API 适配
4. 不负责上下文存储
5. 不负责 SSE 文本序列化
6. 不负责在 schema 中写复杂业务行为

---

## 5. 设计原则

- 契约稳定优先
- 字段含义明确
- 避免把业务逻辑塞进模型
- `/chat` 与 `/chat/stream` 的输入字段应尽量对齐
- stream event payload 与 lifecycle status 枚举必须统一

---

## 6. 当前阶段能力声明

本轮必须新增或补强：

- stream event contract
- `request_id` / `assistant_message_id` / `finish_reason` / `usage` / `latency` / `error_code`
- message lifecycle status 表示
- cancel request contract

当前仍不要求落地：

- tools/function calling contract
- 多模态 contract
- 结构化输出 contract
- 大规模内外 contract 分层重构

---

## 7. 修改规则

1. 修改字段前先评估影响范围
2. 优先做兼容式演进
3. 不要引入对上层模块的依赖
4. 不要把 provider 原始 chunk 当成外部 stream event contract

---

## 8. Code Review 清单

1. 模型命名是否准确？
2. 字段语义是否稳定？
3. lifecycle status 是否统一？
4. cancel 请求是否指向清晰？
5. 是否仍然保持为数据契约层？

---

## 9. 一句话总结

`app/schemas/` 是系统的数据契约层，负责定义同步与流式两条主链路共享的稳定 contract，而不是承担流程、适配或协议序列化逻辑。
