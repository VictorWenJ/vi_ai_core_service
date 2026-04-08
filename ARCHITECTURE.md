# ARCHITECTURE.md

> 更新日期：2026-04-08

## 1. 文档定位

本文件定义 `vi_ai_core_service` 的项目级总体架构。  
本文件只描述仓库层面的系统分层、职责划分、依赖方向、调用关系与演进原则，不展开到模块内部详细实现。

---

## 2. 架构目标

本项目总体架构目标如下：

1. 建立边界清晰的 AI 服务分层结构
2. 让不同能力在不同目录中各司其职
3. 让模型接入、Prompt、Context、编排、API 暴露彼此分离
4. 让系统在后续新增 RAG / Agent / Tool 等能力时具备可扩展性
5. 让协作者与 Codex 能快速判断代码应该落在哪一层

---

## 3. 当前总体架构分层

当前系统按以下七层组织：

### 3.1 API 接入层
对应目录：`app/api/`

职责：

- 暴露 HTTP 接口
- 接收请求
- 做基础输入校验
- 调用应用编排层
- 返回标准响应

### 3.2 应用编排层
对应目录：`app/services/`

职责：

- 串联系统能力模块
- 承接业务用例级流程
- 组织一次完整调用链
- 协调 Context / Prompt / Provider

### 3.3 上下文管理层
对应目录：`app/context/`

职责：

- 管理会话上下文
- 表示历史消息
- 提供上下文管理入口
- 抽象上下文存储
- 承接上下文窗口选择、截断、摘要与序列化策略
- 管理短期记忆的持久化后端与生命周期

### 3.4 Prompt 资产层
对应目录：`app/prompts/`

职责：

- 管理 Prompt 模板资产
- 提供模板注册与查找
- 提供渲染能力
- 支撑多场景 Prompt 演进

### 3.5 模型 API 接入层
对应目录：`app/providers/`

职责：

- 对接不同模型厂商
- 屏蔽厂商协议差异
- 提供统一 provider 抽象
- 管理 provider 注册与发现
- 归一化模型结果

### 3.6 可观测性基础设施层
对应目录：`app/observability/`

职责：

- 提供统一日志上报入口（`log_until.py`）
- 约束统一日志前缀输出
- 约束业务日志体输出
- 为 API / services / providers 提供统一日志上报调用方式

### 3.7 数据模型层
对应目录：`app/schemas/`

职责：

- 定义共享数据契约
- 定义请求模型与响应模型
- 为跨层协作提供稳定数据表示

---

## 4. 总体依赖方向

项目总体依赖方向如下：

`api -> services -> context/prompts/providers -> schemas`

同时：

- `observability` 作为横切基础设施层，可被 `api/services/providers` 等层依赖
- `observability` 不反向依赖业务编排实现

### 运行入口约束

- 唯一运行入口是 `app/server.py`（FastAPI HTTP 服务）
- 对外调用方式是 HTTP 路由（如 `/health`、`/chat`、`/chat/reset`）
- 当前阶段不保留 CLI 直接调用入口

---

## 5. 总体调用关系

当前系统的典型调用思路为：

1. 外部请求进入 API 层
2. API 层将请求委托给应用编排层
3. 应用编排层根据需要：
   - 获取/组装 Context
   - 获取/渲染 Prompt
   - 调用 Provider 发起模型请求
   - 调用 Observability 记录结构化事件与异常信息
4. Provider 返回归一化结果
5. Service 整理结果并返回 API 层
6. API 层输出稳定响应

---

## 5.1 Context Engineering Phase 2 调用链（当前已完成）

Context Engineering Phase 2 已完成默认主链路：

`api -> services/chat_service.py -> services/request_assembler.py -> context/manager.py -> context/stores/* -> context/policies/* -> services/request_assembler.py -> providers/*`

默认上下文治理顺序固定为：

`token-aware selection -> token-aware truncation -> deterministic summary -> serialization`

### 设计说明

1. `app/context/` 负责：
   - canonical context models
   - session history 读取与写回
   - token-aware policy execution
   - history serialization
2. `app/services/request_assembler.py` 负责：
   - 驱动 context policy pipeline
   - 装配 system prompt + history + user input
   - 输出 context assembly trace
3. `app/services/chat_service.py` 负责：
   - 调用 assembler
   - 调用 provider
   - 响应后回写 session history
4. API 层负责：
   - `/chat`
   - `/chat/reset`

---

## 5.2 Context Engineering Phase 3 调用链（当前已落地）

Phase 3 已在保持 Phase 2 默认治理链路不变的前提下，引入**持久化短期记忆后端**与**会话生命周期治理**。  
当前核心调用链分为读路径与写路径。

### 读路径（request-time assembly）

`api -> services/chat_service.py -> services/request_assembler.py -> context/manager.py -> context/stores/{redis_store|in_memory}.py -> context/policies/* -> services/request_assembler.py -> providers/*`

### 写路径（response-time persistence）

`providers/* -> services/chat_service.py -> context/manager.py -> context/stores/{redis_store|in_memory}.py`

### reset 路径

`api/chat.py:/chat/reset -> services/chat_service.py -> context/manager.py -> context/stores/{redis_store|in_memory}.py`

### Phase 3 设计说明

1. **持久化仍属于 context 层内部能力**  
   Redis/持久化细节只允许存在于 `app/context/stores/`，不得泄漏到 `services` 或 `api` 层。

2. **`ContextManager` 继续作为 façade**  
   对上层暴露统一的：
   - `get_context`
   - `append_*`
   - `replace_context_messages`
   - `reset_session`
   - `reset_conversation`
   等能力，不暴露存储细节。

3. **读写路径解耦但契约一致**  
   request-time 使用持久化 session history 做上下文治理；response-time 追加写回仍通过同一 manager/store contract 完成。

4. **生命周期治理进入架构正式范围**  
   Phase 3 中，TTL、key prefix、session/conversation reset 语义、命名空间与序列化版本必须视为正式架构的一部分，而不是临时细节。

6. **配置入口已统一**  
   当前通过 `AppConfig.context_storage_config` 管理存储后端与生命周期配置，包括：
   - `CONTEXT_STORE_BACKEND`
   - `CONTEXT_REDIS_URL`
   - `CONTEXT_SESSION_TTL_SECONDS`
   - `CONTEXT_STORE_KEY_PREFIX`
   - `CONTEXT_ALLOW_MEMORY_FALLBACK`

5. **不引入新系统层**  
   持久化短期记忆仍属于 `app/context/` 的 store 能力升级，不新增 `app/memory/` 层，也不提前引入 `app/rag/`。

---

## 6. 分层设计原则

### 6.1 单层单责

- API 层负责接入
- Service 层负责编排
- Provider 层负责模型适配
- Prompt 层负责模板资产
- Context 层负责上下文与短期记忆治理
- Observability 层负责可观测性基础设施
- Schema 层负责契约定义

### 6.2 下层不反向感知上层

例如：

- `providers` 不应依赖 `services`
- `context` 不应依赖 `api`
- `schemas` 不应依赖任何业务层

### 6.3 专项能力横向分离

Prompt、Context、Provider 应视为平行专项能力，而不是相互嵌套的附属模块。

### 6.4 共享契约稳定

Schema 与 context store contract 必须尽量保持稳定，避免影响多个层的协作与演进。

---

## 7. 根目录与模块目录的架构关系

根目录架构文档负责：

- 定义系统总体层次
- 定义依赖方向
- 定义跨模块架构原则
- 定义新增模块的纳入标准

模块级文档负责：

- 定义本模块内部结构
- 定义本模块内的抽象边界
- 定义本模块局部演进方式
- 定义本模块的详细 review 关注点

---

## 8. 当前目录与架构映射

当前项目目录可按以下方式理解：

- `app/`：主应用代码根目录
- `app/api/`：外部接口接入层
- `app/services/`：应用编排层
- `app/context/`：上下文与短期记忆治理层
- `app/prompts/`：Prompt 资产层
- `app/providers/`：模型接入适配层
- `app/observability/`：可观测性基础设施层
- `app/schemas/`：共享数据契约层
- `tests/`：测试验证层
- `skills/`：工程治理辅助文档层

---

## 9. 当前架构边界约束

当前系统必须遵守以下边界：

1. API 层不得成为业务逻辑堆积层
2. Service 层不得成为 provider 适配层
3. Provider 层不得承担业务主流程
4. Prompt 层不得承担业务控制流
5. Context 层不得承担模型调用
6. Context 层不得承担最终 prompt 装配顺序
7. Observability 层不得承担业务流程或 provider 接入逻辑
8. Schema 层不得承担业务逻辑
9. Redis/持久化 store 不得泄漏到 `services` / `api` 的直接实现中

---

## 10. 可扩展架构原则

未来潜在扩展方向包括：

- `app/rag/`
- `app/agents/`
- `app/tooling/`
- `app/evaluation/`
- integration tests / e2e tests

这些新模块进入项目时，必须满足：

1. 与现有层职责不重复
2. 能解释清楚依赖方向
3. 不破坏当前七层主结构
4. 有相应模块级文档约束

### Context 与 RAG 的未来边界

- `app/context/` 负责 conversation/session short-term memory
- `app/rag/` 负责 knowledge retrieval / grounding
- 两者都可为 request assembly 提供上下文，但职责不同、边界不可混淆

---

## 11. 当前架构优先保证什么

当前阶段，架构最优先保证的是：

- 分层正确
- 调用链清晰
- 模块不混写
- Provider / Prompt / Context 三类能力正确分离
- 持久化短期记忆的 store 升级不打穿现有边界
- request assembly 中的上下文治理路径稳定、明确、可测试
- 文档治理与代码结构一致

---

## 12. 当前架构暂不追求什么

当前阶段暂不追求：

- 长期记忆平台
- 向量检索
- 复杂语义召回
- 新系统层的大规模扩张
- 把短期记忆 persistence 直接包装成“memory platform”

---

## 13. 一句话总结

`vi_ai_core_service` 当前采用七层治理式 AI 服务架构。  
Phase 2 已完成 token-aware 上下文主链路；Phase 3 将在不新增系统层的前提下，把 `app/context/` 从“单实例内存骨架”升级为“持久化短期记忆能力”，同时保持与未来 `app/rag/` / 长期记忆的边界清晰。

---

## 14. 架构治理执行顺序

1. 项目级约束：根目录四文档
2. 模块级约束：目标模块 `AGENTS.md`
3. 任务级做法：对应 skill 文档
4. 代码实现：仅在分层边界内落地
5. 架构审查：按 `CODE_REVIEW.md` 做边界与依赖检查
6. 文档回写：保持文档事实与代码现实一致

### Phase 3 专项执行顺序

1. 先定义持久化 store contract 与配置边界
2. 再实现 `RedisContextStore`（保留 `InMemoryContextStore` 作为 fallback）
3. 再打通 manager / service / API 的持久化读写路径
4. 再补 TTL / reset / namespace 语义
5. 最后补测试与文档回写

不允许先在 `chat_service.py` 直接写 Redis 逻辑，再反推 store 抽象。
