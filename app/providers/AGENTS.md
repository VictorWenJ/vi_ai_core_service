# app/providers/AGENTS.md

> 更新日期：2026-04-09

## 1. 文档定位

本文件定义 `app/providers/` 的职责、边界、结构约束与 review 标准。  
当前阶段，本文件临时同时承担该模块的 AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW 职责。

---

## 2. 模块定位

`app/providers/` 是系统的模型 API 接入层。  
它负责对接不同模型厂商，实现统一 provider 抽象，并向上层暴露一致的模型调用能力。

---

## 3. 本层职责

1. 定义 provider 统一抽象
2. 对接不同厂商模型接口
3. 将内部请求映射到厂商请求
4. 将厂商响应归一化为系统内部结果
5. 将厂商流式 chunk / finish / usage / error 归一化为系统内部 stream contract
6. 管理 provider 注册与查找

---

## 4. 本层不负责什么

1. 不负责 HTTP API 暴露
2. 不负责业务流程编排
3. 不负责上下文存储
4. 不负责 SSE 文本序列化
5. 不负责 assistant message 生命周期状态机
6. 不负责 cancel 接口或 request registry

---

## 5. 架构原则

### 5.1 统一抽象优先
系统内部必须围绕统一 provider 抽象设计，而不是围绕单一厂商 SDK 设计。

### 5.2 协议差异向下吸收
厂商差异应尽量在 provider 层被吸收，不要外溢到 service 层或 API 层。

### 5.3 流式与非流式都要归一化
Phase 5 中，provider 不再只要求非流式文本 chat 主路径，还必须支持文本 streaming 的统一归一化。

### 5.4 provider 只输出 canonical stream，不输出 SSE
provider 负责 chunk / finish / usage / provider error 的 canonical 化，不负责 `event:` / `data:` 这类 SSE 文本协议。

---

## 6. 当前阶段能力声明

本轮必须新增或补强：

- 文本 streaming 真实路径
- provider streaming chunk 归一化
- finish_reason / usage / provider error 的流式收口字段
- streaming 与 non-streaming 的统一抽象关系

当前仍不要求落地：

- 多模态真实输入映射
- tools/function calling
- 结构化输出
- 自动 fallback / retry / routing 引擎

---

## 7. 修改规则

1. 不允许把厂商私有逻辑泄漏到上层
2. 不允许影响现有 registry 行为
3. 不允许把 SSE 或生命周期状态机塞进 provider
4. 不允许 streaming 实现破坏 non-streaming 主路径

---

## 8. Code Review 清单

1. 是否仍围绕统一 provider 抽象实现？
2. chunk 增量是否归一化清晰？
3. finish / usage / error 是否可被上层稳定理解？
4. 是否没有直接暴露厂商原始事件流？
5. streaming 与 non-streaming 是否共享合理的 canonical contract？

---

## 9. 测试要求

至少覆盖：

1. provider 注册与发现
2. 非流式请求/响应归一化
3. 流式 chunk 归一化
4. 流式 finish / usage / error 收口
5. OpenAI 兼容基类复用行为

---

## 10. 一句话总结

`app/providers/` 在 Phase 5 中的职责是把厂商侧的非流式与流式文本生成都吸收到统一 provider 抽象下，并向 services 提供稳定的 canonical response / stream chunk，而不是承担 SSE 或业务生命周期编排。
