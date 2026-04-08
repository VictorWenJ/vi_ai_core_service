# app/api/AGENTS.md

> 更新日期：2026-04-08

## 1. 文档定位

本文件定义 `app/api/` 目录的职责、边界、结构约束、演进方向与代码审查标准。  
当前阶段，本文件临时同时承担该模块的 AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW 职责。

---

## 2. 模块定位

`app/api/` 是系统的 **API 接入层**。  
它负责将外部 HTTP 请求接入系统，并将内部应用编排能力暴露为稳定、清晰、可测试的接口。

当前目录中重点包括：

- `chat.py`
- `health.py`
- `schemas/chat.py`
- `deps.py`
- `error_mapping.py`

---

## 3. 本层职责

1. 定义 HTTP 路由与接口入口
2. 接收并解析请求
3. 做接口层输入校验与基础错误处理
4. 调用 `app/services/`
5. 将内部结果映射为外部响应
6. 输出标准化 HTTP 状态码与错误语义

---

## 4. 本层不负责什么

1. 不负责模型厂商 API 适配
2. 不负责 Prompt 模板渲染细节
3. 不负责 context store 的持久化实现
4. 不负责具体业务流程编排
5. 不负责 provider 选择与 provider fallback
6. 不负责直接访问 Redis 或其他存储后端

---

## 5. 依赖边界

### 允许依赖

- `app/services/`
- `app/schemas/`
- 必要的框架基础设施（FastAPI）
- 少量接口层必要配置

### 禁止直接依赖

- `app/context/stores/*`
- `app/providers/` 作为常规调用路径
- `app/prompts/` 作为常规调用路径
- Redis client 或 key 规则

---

## 6. 当前建议结构

API 层维持“薄路由”结构：

- `chat.py`
  - `/chat`
  - `/chat/reset`
- `schemas/`
  - 请求/响应 schema
- `deps.py`
  - service 装配与依赖入口
- `error_mapping.py`
  - service 异常到 HTTP 语义映射
- `health.py`
  - liveness/readiness/basic health

后续若有真实需求，再考虑 conversation 管理类接口，但本阶段不做大扩张。

---

## 7. 设计原则

### 7.1 薄路由原则

每个路由函数应尽量只包含：

- 请求接收
- 参数校验
- 调用 service
- 返回响应

### 7.2 持久化细节不进入路由层

Phase 3 中 API 层可以暴露与 session / conversation 相关的接口，但绝不直接操作持久化 store。

### 7.3 响应结构稳定

同一类接口响应结构应保持稳定，不随内部实现频繁变更。

---

## 8. 当前阶段能力声明

- 已实现并验收：
  - `/health`
  - `/chat`
  - `/chat/reset`
  - 基础输入校验与错误映射
- 当前已落地：
  - `/chat` 与 `/chat/reset` 在持久化短期记忆（Redis backend）场景下保持稳定
  - API 层继续通过 service 调用，不直接触达 Redis/store 细节
- 当前不要求落地：
  - streaming 接口
  - 多模态接口
  - conversation CRUD 全家桶
  - 管理后台接口

---

## 9. 修改规则

1. 不允许在 API 层读写 store 私有状态
2. 不允许在路由里拼接 Redis key 或设置 TTL
3. 不允许在路由里手写上下文治理逻辑
4. 必须把核心流程委托给 `app/services/`
5. 变更接口契约必须同步更新 schema、测试与文档

---

## 10. Code Review 清单

1. 路由层是否保持薄？
2. 是否越层调用 context store / Redis？
3. 请求/响应结构是否稳定？
4. 错误信息是否清晰？
5. reset 接口语义是否仍然正确？
6. 是否破坏现有 `/chat` 与 `/chat/reset` 契约？

---

## 11. 测试要求

至少覆盖：

1. `/health` 成功路径
2. `/chat` 成功路径
3. `/chat/reset` session 路径
4. `/chat/reset` conversation 路径
5. service 抛错后的错误映射路径

---

## 12. 一句话总结

`app/api/` 的职责是**接入、校验、转发、返回**。  
进入 Phase 3 后，这一点不变；变化的是服务层和 context 层会在 API 背后接入持久化短期记忆，但这些细节不应泄漏到路由层。

---

## 13. 本模块任务执行链路（强制）

1. 根目录四文档
2. 本文件
3. `app/services/AGENTS.md` 与 `app/context/AGENTS.md`
4. 对应 skill 文档
5. 修改 API 代码
6. 更新测试与文档回写

---

## 14. 本模块交付门禁

- 发现 API 越层调用 context store / Redis，必须先整改
- 变更影响主链路时，必须补充或更新 API 测试
- 未通过 `python-api-capability` checklist，不视为完成
