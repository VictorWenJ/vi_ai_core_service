# app/services/AGENTS.md

> 更新日期：2026-04-09

## 1. 文档定位

本文件定义 `app/services/` 目录的职责、边界、结构约束、演进方向与代码审查标准。  
当前阶段，本文件临时同时承担该模块的 AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW 职责。

---

## 2. 模块定位

`app/services/` 是系统的 **应用编排层**。  
它负责串联 API 接入层与底层能力模块（context、prompts、providers），完成一次业务请求的主执行流程。

当前目录下已有：

- `chat_service.py`
- `request_assembler.py`
- `llm_service.py`
- `prompt_service.py`

---

## 3. 本层职责

1. 承接 API 层传入的用例请求
2. 组织一次完整调用链路
3. 协调 `app/context/`、`app/prompts/`、`app/providers/`
4. 将底层能力拼装为可用业务流程
5. 做跨模块的流程控制、失败传播与结果封装
6. 在 Phase 4 中承接分层短期记忆的读写编排

---

## 4. 本层不负责什么

1. 不负责 HTTP 路由定义
2. 不负责底层 provider HTTP/SDK 适配细节
3. 不负责 Prompt 模板文件资产管理细节
4. 不负责 context store 的底层存储实现
5. 不负责定义基础数据模型契约本身
6. 不负责在 service 内部直接写 Redis / key prefix / TTL / scope 细节
7. 不负责把 working memory reducer 变成业务规则中心

---

## 5. 依赖边界

### 允许依赖

`app/services/` 可以依赖：

- `app/context/`
- `app/prompts/`
- `app/providers/`
- `app/schemas/`
- 必要的配置模块

### 禁止依赖

`app/services/` 不应依赖：

- `app/api/`
- store 私有实现细节（例如 Redis key 拼接、原始 Redis client）

---

## 6. 当前结构理解

- `chat_service.py`
  - 主 LLM chat 编排入口
  - 协调 context / prompt / provider 主链路
  - 在响应后通过 manager/store 回写 layered memory state
- `request_assembler.py`
  - 承载请求装配与规范化
  - 是 Phase 2/3/4 的正式上下文装配入口
- `llm_service.py`
  - 兼容导出入口
- `prompt_service.py`
  - 提供 prompt 获取、选择、渲染的面向应用层封装

---

## 7. 架构原则

### 7.1 编排优先，细节下沉

services 负责“编排”，不负责“底层实现”。

### 7.2 request_assembler 是上下文装配中枢

- `request_assembler.py` 负责读取并治理 layered memory
- `chat_service.py` 负责主流程协调与结果回写
- `app/context/` 负责 state representation、policy execution、reducer、rendering 与 store lifecycle

### 7.3 Phase 4 的固定装配顺序必须收敛在 assembler

assembler 是唯一允许决定以下顺序的地方：

1. system prompt
2. working memory block
3. rolling summary block
4. recent raw messages
5. current user input

### 7.4 Phase 4 的持久化读写由 service 统一调度

在 Phase 4 中：

- 读路径：service -> request_assembler -> context manager -> persistent store
- 写路径：service -> context manager / reducer -> persistent store
- reset 路径：service -> context manager -> persistent store

但 service 不直接接触 Redis client、key 细节或 store codec。

---

## 8. 当前阶段能力声明（强约束）

- 已实现并验收：
  - 非流式 LLM 主链路编排
  - Prompt / Context / Provider 的最小协作
  - `request_assembler.py` 的上下文装配中枢职责
  - token-aware 历史治理与 reset 流程
  - 持久化短期记忆读写编排
- 当前本轮要落地：
  - conversation-scoped layered memory 读取与回写编排
  - request assembly 中 working memory / rolling summary / recent raw 的固定顺序
  - response 后统一更新 recent raw、rolling summary 与 working memory
  - `ContextManager.from_app_config` + `ContextPolicyConfig` + `ContextStorageConfig` + `ContextMemoryConfig` 的装配链路
- 仍不要求落地：
  - streaming
  - 多模态
  - RAG / 长期记忆
  - 跨模块工作流系统

---

## 9. 修改规则

1. 不允许在 service 层直接调用 Redis client
2. 不允许在 service 层手写 key prefix / TTL / scope 逻辑
3. 不允许把上下文治理细节重新塞回 `chat_service.py`
4. 不允许让 `request_assembler.py` 直接依赖 store 私有实现
5. 不允许在 service 层自己决定 summary merge 或 reducer 的底层算法
6. 改动主链路时必须同步更新测试与文档

---

## 10. Code Review 清单

1. service 是否仍然是编排层，而非存储实现层？
2. 是否绕过 `ContextManager` 直接操作 store？
3. request-time 读路径与 response-time 写路径是否一致且清晰？
4. 是否存在直接拼接 Redis key、手写 TTL / scope 等越界实现？
5. request assembly 顺序是否仍固定为 `system -> working_memory -> rolling_summary -> recent_raw -> user`？
6. 错误传播与 observability 是否保持稳定？
7. reset / append / replace / update_state 语义是否通过 service 正确协调？

---

## 11. 测试要求

至少覆盖：

1. `chat_from_user_prompt` 主链路成功路径
2. `request_assembler` 读取 layered memory 并按固定顺序装配
3. 响应后 user / assistant recent raw 历史写回
4. recent raw 超预算时 rolling summary 触发更新
5. working memory reducer 更新后的持久化写回
6. `reset_context` session / conversation 两条路径
7. Redis store 不可用时的预期行为（若实现了 fallback）

---

## 12. 一句话总结

`app/services/` 在 Phase 4 中的职责不是“实现 layered memory 算法”，而是**把 conversation-scoped layered short-term memory 稳定地编排进现有主链路**。  
服务层只调度，不持有存储细节。

---

## 13. 本模块任务执行链路（强制）

1. 根目录四文档
2. 本文件
3. `app/context/AGENTS.md` 与 `skills/python-context-capability/SKILL.md`
4. 修改 service 代码
5. 更新测试与文档回写

---

## 14. 本模块交付门禁

- 发现 service 直连 Redis/store 私有实现，必须先整改
- 主链路改动未补测试，不视为完成
- 未明确读路径 / 写路径 / reset 路径，不允许合并 Phase 4 代码
- 未保持 assembler 顺序中枢职责，不允许合并
