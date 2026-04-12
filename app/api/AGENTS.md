# app/api/AGENTS.md

> 更新日期：2026-04-13

## 1. 文档定位

本文件定义 `app/api/` 的职责、边界、结构约束、开发约束与 review 标准。
当前阶段，本文件临时同时承担该模块的 `AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW` 职责。
执行 api 相关任务时，必须先读根目录 `AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md`，再读本文件，再根据 skill `skills/python-api-capability/` 执行。

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

`app/api/` 是系统的 HTTP / SSE 接入层。
它负责对外暴露同步与流式接口，解析请求，调用 services，并返回稳定的数据契约。

当前阶段建议围绕以下职责组织：

- `chat.py`：`/chat`、`/chat_stream`、`/chat_stream_cancel`、`/chat_reset`
- `knowledge.py`：`/knowledge/*` 相关控制面入口
- `evaluation.py`：`/evaluation/*` 相关控制面入口
- `runtime.py`：`/runtime/*` 相关摘要入口
- `health.py`：`/health`
- `deps.py`：依赖装配
- `error_mapping.py`：异常到 HTTP 的映射
- `sse.py`：SSE 文本序列化
- `schemas/`：按领域维护 API 层请求 / 响应模型

---

## 3. 本模块职责

1. 解析请求参数
2. 进行 schema 校验
3. 调用对应 service
4. 返回 JSON 响应
5. 输出 SSE 事件流
6. 保持对外契约稳定
7. 维护 `/chat`、`/chat_stream`、`/chat_stream_cancel`、`/chat_reset`、`/health` 的稳定接入语义
8. 维护 knowledge / evaluation / runtime 控制面 API 的稳定领域契约

---

## 4. 本模块不负责什么

1. 不负责 chat 主用例编排
2. 不负责 assistant message lifecycle 状态机实现
3. 不负责 retrieval query 构建
4. 不负责 parser / chunker / embedding / index / retrieval
5. 不负责 citations 生成逻辑
6. 不负责 context state 更新
7. 不负责 provider 原始 chunk 处理细节

---

## 5. 依赖边界

### 允许依赖
- `app/services/`
- `app/api/schemas/`
- `app/observability/`

### 禁止依赖
- `app/context/`
- `app/providers/`
- `app/rag/`
- Redis / Qdrant / embedding provider 的底层 SDK

---

## 6. 架构原则

### 6.1 API 只做协议，不做业务编排
API 负责收与发，不负责 chat、streaming、retrieval 的内部流程。

### 6.2 同步与流式契约都要稳定
- `/chat` 返回 JSON
- `/chat_stream` 返回 `text/event-stream`

### 6.3 当前代码中的 API 契约事实
- `/chat` 当前返回：`content`、`provider`、`model`、`usage`、`finish_reason`、`metadata`、`raw_response`
- `/chat` 当前还返回：`citations`
- `/chat_stream` 当前输出：`response.started`、`response.delta`、`response.completed`、`response.error`、`response.cancelled`、`response.heartbeat`
- `response.completed` 当前可携带 `usage`、`latency_ms`、`trace`、`citations`
- delta 阶段不输出 citation 增量
- `/chat` 当前统一调用 `chat_with_citations_from_user_prompt`，不再保留历史 `hasattr` 兼容分支

### 6.4 外部契约不泄漏内部实现细节
不应把：
- Qdrant collection
- embedding model 内部细节
- 向量维度
- 检索后端 SDK 结构
- context store scope 细节

直接暴露到 API 响应中。

### 6.5 SSE 序列化属于 API 协议职责
- SSE 文本格式化应留在 API 层
- SSE event name 与 payload 结构必须稳定
- API 层不负责定义业务生命周期状态机，但负责正确输出其协议表示

### 6.6 API 命名必须按领域，而不是按消费者
- 路由文件与 URL 分组应按领域职责命名，例如 `knowledge.py`、`evaluation.py`、`runtime.py`
- 不再以 `*_console.py` 作为正式 API 文件名
- 前端 Internal Console 只是当前消费者，不能反向定义后端 API 模块命名

### 6.7 前后端契约统一原则
- 后端 schema 是前后端契约的 source of truth
- 前端 API client 与类型定义应围绕后端领域 schema 对齐
- 控制面 API 继续采用 REST JSON；chat 保持 JSON + SSE 双协议

### 6.8 持久化升级下的契约稳定原则
- 底层从内存控制面切换到 MySQL 控制面时，API 应尽量保持领域路径与主要响应形状稳定
- `app/api/schemas/` 只承载对外 request / response contract
- 不得把 repository model、ORM model、内部 persistence 对象直接暴露给 API

## 7. 当前阶段能力声明


当前本轮必须保持稳定：

- `/chat`
- `/chat_stream`
- `/chat_stream_cancel`
- `/chat_reset`
- `/health`
- started / delta / completed / error / cancelled / heartbeat 事件语义
- 同步与流式 chat 主链路

当前代码事实补充：

- `ChatResponse` 已定义 `citations`
- `response.completed` 已定义 `citations`
- 当前控制面 API 已按领域分组为 knowledge / evaluation / runtime，而不是按 console 消费者命名
- API 层仍不直接接入 retrieval，仅消费 service 编排结果与降级结果

当前本轮必须保持：

- citations 通过稳定 schema 输出
- `chat_stream` 仅在 completed 事件携带 citations
- API 层不得自行拼装 retrieval / citation 业务语义

---

## 8. 文档维护规则（强约束）

本文件属于 `app/api/` 模块的治理模板资产。
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
如果未来需要升级 `app/api/AGENTS.md` 的模板，必须先明确说明这是一次“模板升级”，并在确认后再统一应用。
在未确认是“模板升级”前，默认只允许做增量更新，不允许重写模板。

---

## 9. 修改规则

1. 不允许在 API 层直接访问向量库
2. 不允许在 API 层直接构建 retrieval query
3. 不允许在 API 层直接组织 knowledge block
4. 不允许在 API 层生成 citations 内容
5. 若未来新增 citations，不允许以无 schema、临时拼接字段的方式输出
6. 不允许在 API 层直接做 context reset / cancel / stream 之外的状态机编排
7. 不允许为历史测试保留旧 service 方法名的双轨调用分支
8. 不允许新增 `*_console.py` 形式的正式 API 文件名
9. 不允许把控制面 API 设计成仅服务 Internal Console 的临时命名或临时响应结构

---

## 10. Code Review 清单

- route handler 是否仍保持薄路由？
- 是否把底层持久化切换限制在 service / rag 子域内部，而不是泄漏到 API 契约？
- 新增字段是否遵守 `*_details` / `*_ids` 命名语义？
- 是否避免按 console / playground 命名长期对外接口？


1. API 是否仍然只负责协议输入输出？
2. 是否没有把 retrieval / context / provider 逻辑混到 API 层？
3. `/chat` 当前返回字段是否仍与 `app/api/schemas/chat.py` 一致？
4. `/chat_stream` 当前事件集合与 payload 是否仍与 service 输出一致？
5. delta 阶段是否仍保持轻量、稳定且不带 citations？
6. `/chat_stream_cancel` 语义是否清晰且稳定？
7. `/chat_reset` 是否只承担接入层职责？
8. 是否没有把未落地的 Phase 6 能力写成已实现事实？
9. 是否没有泄漏底层向量库与 embedding 细节？
10. 本次文档更新是否遵守了“文档维护规则”？
11. 控制面 API 是否已按领域命名收敛，而不是保留 `*_console` 命名？
12. 是否保持了原有布局、排版、标题层级、写法和风格？

---

## 11. 测试要求

- knowledge / evaluation / runtime 路由在底层切换后仍保持 contract 稳定的测试
- 文档详情、build 详情、evaluation run 详情新增字段的契约测试
- Inspector 向量详情接口或字段的协议测试（若本轮新增）


至少覆盖：

1. `/chat` 正常返回 `ChatResponse`
2. `/chat` citations 输出与空数组行为
3. `/chat_stream` started / delta / completed 事件输出
4. `/chat_stream` completed citations 输出，delta 不输出 citations
5. retrieval 失败时 chat/stream 仍成功
6. `/chat_stream_cancel` 行为符合设计
7. `/chat_reset` 行为符合设计
8. `error_mapping.py` 映射稳定
9. `/health` 与 HTTP smoke 行为符合设计
10. 原有同步与流式契约未被破坏
11. knowledge / evaluation / runtime 控制面 API 契约稳定且按领域命名

---

## 12. 一句话总结

`app/api/` 在当前代码基线中只负责同步 JSON 与 SSE 文本协议接入、错误映射与稳定契约输出；citations 仅作为契约字段透传，不承接 retrieval 业务语义，并在后续更新中严格遵守模块文档的模板冻结规则。
