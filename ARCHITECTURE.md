# ARCHITECTURE.md

> 更新日期：2026-04-09

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
5. 让协作者与 Codex 能快速判断代码应该落在哪一层或哪个治理域

---

## 3. 当前总体架构分层

当前系统按以下七层业务/系统分层组织：

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
- 管理 conversation-scoped 短期上下文状态
- 表示 recent raw messages / rolling summary / working memory
- 提供统一上下文管理入口
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
- 提供统一日志上报入口
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

## 4. 工程基础设施平面（非业务分层）

除上述七层外，项目存在一个**工程基础设施平面**，当前对应目录为：

- `infra/`

### 4.1 `infra/` 的职责

`infra/` 不属于业务系统分层，不进入 `api -> services -> context/prompts/providers -> schemas` 的业务依赖链。  
它负责：

- Dockerfile
- compose 编排
- app + redis 本地联调
- 运行时环境变量样例
- 开发/测试/交付运行方式说明

### 4.2 `infra/` 的边界

`infra/` 不负责：

- 业务逻辑
- Provider 适配
- Context policy
- Prompt 模板
- API / service 主链路实现

业务代码可以通过配置连接 Redis，但不能在运行时依赖 `infra/` 中的脚本或 compose 文件。

---

## 5. 总体依赖方向

业务依赖方向如下：

`api -> services -> context/prompts/providers -> schemas`

同时：

- `observability` 作为横切基础设施层，可被 `api/services/providers` 等层依赖
- `observability` 不反向依赖业务编排实现
- `infra/` 不参与业务依赖链，只提供运行时交付支撑

### 运行入口约束

- 唯一业务运行入口是 `app/server.py`（FastAPI HTTP 服务）
- 对外调用方式是 HTTP 路由（如 `/health`、`/chat`、`/chat/reset`）
- 本地推荐运行方式为 Docker Compose（app + redis）
- 当前阶段不保留 CLI 直接调用入口

---

## 6. 总体调用关系

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

## 6.1 Context Engineering Phase 2 调用链（已完成）

默认上下文治理顺序固定为：

`token-aware selection -> token-aware truncation -> deterministic summary -> serialization`

调用链：

`api -> services/chat_service.py -> services/request_assembler.py -> context/manager.py -> context/stores/* -> context/policies/* -> services/request_assembler.py -> providers/*`

---

## 6.2 Context Engineering Phase 3 调用链（已落地）

Phase 3 在保持 Phase 2 默认治理链路不变的前提下，引入**持久化短期记忆后端**与**会话生命周期治理**。

### 读路径（request-time assembly）

`api -> services/chat_service.py -> services/request_assembler.py -> context/manager.py -> context/stores/{redis_store|in_memory}.py -> context/policies/* -> services/request_assembler.py -> providers/*`

### 写路径（response-time persistence）

`providers/* -> services/chat_service.py -> context/manager.py -> context/stores/{redis_store|in_memory}.py`

### reset 路径

`api/chat.py -> services/chat_service.py -> context/manager.py -> context/stores/{redis_store|in_memory}.py`

### 设计说明

1. `ContextManager` 继续作为 façade，对上暴露统一 contract
2. `BaseContextStore` 定义 backend 统一契约
3. `InMemoryContextStore` 作为开发/测试 fallback
4. `RedisContextStore` 作为 Phase 3 持久化短期记忆实现
5. `request_assembler.py` 仍是正式上下文装配入口
6. `infra/` 只负责 app + redis 的运行编排，不进入业务主链路

---

## 6.3 Context Engineering Phase 4 调用链（已落地）

Phase 4 在保持 Phase 2 policy pipeline 与 Phase 3 persistence contract 基础上，引入**conversation-scoped layered short-term memory**。

### 6.3.1 上下文主作用域

从本轮开始，context 读写与持久化的主作用域应统一为：

`(session_id, conversation_id)`

其中：

- `session_id`：用户会话容器
- `conversation_id`：当前对话线程
- 当 `conversation_id` 缺失时，store 内部可以使用默认 scope（例如 `__default__`），但该默认值只属于 context store 内部实现细节，不应泄漏到 API 契约层

### 6.3.2 分层短期记忆模型

Phase 4 的 `ContextWindow` 不再只表示“消息列表”，而是表示 conversation-scoped state：

- `messages`：仅表示 recent raw messages
- `rolling_summary`：表示已被 recent raw 挤出的旧历史的滚动摘要
- `working_memory`：表示当前会话形成的结构化工作记忆
- `runtime_meta`：表示 scope、版本、计数、压缩等运行元信息

### 6.3.3 读路径（request-time assembly）

`api -> services/chat_service.py -> services/request_assembler.py -> context/manager.py -> context/stores/{redis_store|in_memory}.py -> context/policies/* -> context/rendering.py -> services/request_assembler.py -> providers/*`

其中 request assembly 的固定顺序为：

1. system prompt
2. working memory block
3. rolling summary block
4. recent raw messages（经过 Phase 2 policy pipeline）
5. current user input

### 6.3.4 写路径（response-time state update）

`providers/* -> services/chat_service.py -> context/manager.py -> context/memory_reducer.py -> context/stores/{redis_store|in_memory}.py`

其中 response-time 更新顺序为：

1. 追加本轮 user / assistant recent raw messages
2. 判断 recent raw 是否超过预算
3. 将较老消息压入 rolling summary
4. 通过 working memory reducer 更新结构化短期记忆
5. 持久化整个 conversation-scoped state

### 6.3.5 reset 路径

`api/chat.py -> services/chat_service.py -> context/manager.py -> context/stores/{redis_store|in_memory}.py`

reset 语义保持：

- reset conversation：仅清当前 `(session_id, conversation_id)` scope
- reset session：清当前 `session_id` 下全部 conversation scope

---

## 7. 根目录与模块目录的架构关系

根目录架构文档负责：

- 定义系统总体层次
- 定义依赖方向
- 定义跨模块架构原则
- 定义新增模块/治理域的纳入标准

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
- `infra/`：工程基础设施/运行时交付目录（非业务系统分层）

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
10. `infra/` 不得承担任何业务逻辑
11. Phase 4 中 `context/rendering.py` 只能负责 provider-agnostic block 渲染，不得在 context 层决定最终 assembly 顺序
12. Phase 4 中 `working_memory` / `rolling_summary` 仍属于 short-term memory，不得偷换成 long-term memory / retrieval memory

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
- Phase 4 只允许在 `app/context/` 内形成分层短期记忆，不允许预先落地向量检索链路

---

## 11. 当前架构优先保证什么

当前阶段，架构最优先保证的是：

- 分层正确
- 调用链清晰
- 模块不混写
- Provider / Prompt / Context 三类能力正确分离
- 持久化短期记忆的 store 升级不打穿现有边界
- request assembly 中的上下文治理路径稳定、明确、可测试
- Phase 4 的 scope 隔离与 layered memory 语义清晰
- Docker / compose 只承担运行时职责，不污染业务代码
- 文档治理与代码结构一致

---

## 12. 当前架构暂不追求什么

当前阶段暂不追求：

- 长期记忆平台
- 向量检索
- 复杂语义召回
- 新系统层的大规模扩张
- 把短期记忆 persistence 直接包装成“memory platform”
- 自建复杂容器平台或生产级编排系统
- 第二次 LLM 调用的语义摘要 / 记忆抽取框架

---

## 13. 一句话总结

`vi_ai_core_service` 当前采用七层治理式 AI 服务架构，并在其外建立 `infra/` 作为工程基础设施平面。  
Phase 2 已完成 token-aware 上下文主链路；Phase 3 已把 `app/context/` 升级为持久化短期记忆能力；当前 Phase 4 的目标是把它继续升级为 **conversation-scoped layered short-term memory**，同时保持与未来 `app/rag/` 的边界清晰。

---

## 14. 架构治理执行顺序

1. 项目级约束：根目录四文档
2. 模块级约束：目标模块 `AGENTS.md`
3. 任务级做法：对应 skill 文档（若存在）
4. 代码实现：仅在分层边界内落地
5. 架构审查：按 `CODE_REVIEW.md` 做边界与依赖检查
6. 文档回写：保持文档事实与代码现实一致

### Phase 4 专项执行顺序

1. 先定义 `(session_id, conversation_id)` scope 与 `ContextWindow` 新语义
2. 再实现 `rolling_summary` / `working_memory` 的模型与持久化编码
3. 再实现 reducer / rendering / manager contract 升级
4. 再打通 `request_assembler.py` 读路径与 `chat_service.py` 写路径
5. 再补 trace / reset / TTL / 配置语义
6. 最后补测试与文档回写

### Infra 专项执行顺序

1. 先定义 `infra/` 职责与边界
2. 再实现 Dockerfile / compose / env 样例
3. 再验证 app + redis 联调
4. 最后补说明文档与 review 约束

不允许先把 Redis/Docker 细节散落写进业务代码，再反推架构边界。

---

## 15. 当前配置约束（2026-04-09）

1. 根目录 `.env.example` 是当前阶段唯一配置文件。
2. 代码默认直接读取根目录 `.env.example`。
3. `infra/compose.yaml` 直接读取根目录 `.env.example`。
4. 当前阶段不再使用 `.env`。
5. 当前阶段不处理 API key 安全治理；密钥治理与生产配置分层后续独立阶段处理。
6. Phase 4 应将 context 相关配置按职责分开治理：
   - `ContextPolicyConfig`：请求时窗口治理
   - `ContextStorageConfig`：持久化后端 / TTL / prefix / fallback
   - `ContextMemoryConfig`：recent raw / rolling summary / working memory 的层级治理
