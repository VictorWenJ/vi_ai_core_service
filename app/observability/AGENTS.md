# app/observability/AGENTS.md

> 更新日期：2026-04-09

## 1. 文档定位

本文件定义 `app/observability/` 的职责边界、设计原则、演进约束与 review 标准。  
执行 observability 相关任务时，必须先读根目录四文档，再读本文件，再执行 `skills/python-observability-capability/`。

---

## 2. 模块定位

`app/observability/` 是系统的最小可观测性基础设施层。  
当前阶段核心仍不是平台化 observability，而是统一日志能力与流式会话生命周期定位能力。

---

## 3. 本层职责

1. 提供统一日志上报入口
2. 统一日志格式与结构化 JSON 输出
3. 提供最小对象序列化支持
4. 为 Phase 5 提供流式会话定位字段约束

### Phase 5 必须覆盖的流式定位字段

- `request_id`
- `session_id`
- `conversation_id`
- `assistant_message_id`
- `streaming`
- `status`
- `stream_event_count`
- `provider`
- `model`
- `finish_reason`
- `latency_ms`
- `error_code`

---

## 4. 本层不负责什么

1. 不负责 request middleware 平台化建设
2. 不负责 tracing / metrics / alerting / APM
3. 不负责业务流程编排
4. 不负责 SSE 事件驱动
5. 不负责取消注册表或生命周期状态机

---

## 5. 设计原则

- 标准库优先：继续使用 `logging`
- 前缀稳定、业务 JSON 结构化
- Phase 5 只补观测字段，不升级成 tracing 平台
- 严格避免敏感信息泄漏

---

## 6. 当前阶段能力声明

本轮必须新增或补强：

- 流式链路日志字段约束
- started / completed / error / cancelled 的结构化记录
- request_id / assistant_message_id 等定位信息的贯穿

当前仍不要求落地：

- tracing / metrics / alerting / APM
- 中间件式自动 request context 注入平台
- 链路可视化平台

---

## 7. 修改规则

1. 不把业务编排逻辑放进 observability
2. 不绕开统一输出格式约束
3. 不在 observability 层处理 SSE、取消控制或 provider chunk 聚合
4. 若新增字段或格式规则，必须同步更新根文档、模块文档与 skill

---

## 8. Code Review 清单

1. 是否仍使用标准库 `logging`
2. 是否仍满足前缀 + `message=<json>` 输出格式
3. started / completed / error / cancelled 日志字段是否可定位
4. 是否输出了敏感凭据字段
5. 是否引入了当前阶段无关的平台化能力

---

## 9. 一句话总结

当前 `app/observability/` 的职责是为同步与流式两条主链路提供统一、可解析、可定位的结构化日志基础设施，而不是承担 tracing 平台或业务状态机。
