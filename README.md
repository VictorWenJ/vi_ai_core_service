# vi_ai_core_service

> 更新日期：2026-04-08

`vi_ai_core_service` 是 VI AI Project 的 Python AI Core 子系统，面向 C 端 AI 应用后端能力建设。

当前阶段重点是：在清晰分层和文档治理下，稳定单轮非流式主链路，并完成短期会话上下文的持久化能力。

## 当前阶段状态

当前代码现实为：

- Phase 2 已完成：token-aware context pipeline（selection -> truncation -> deterministic summary -> serialization）
- Phase 3 已完成主链路：持久化短期记忆（Redis backend / store factory / TTL / reset）
- `infra/` 已纳入治理：支持 app + redis Docker Compose 本地联调
- HTTP-only 调用方式：统一入口 `app/server.py`
- 根目录 `.env.example` 是当前阶段唯一配置文件（代码与 compose 都直接读取）
- 当前仍未进入 Phase 4（长期记忆 / RAG / retrieval 阶段）

## 当前已实现能力

- `/health`、`/chat`、`/chat/reset` 路由
- API -> services -> context/prompts/providers -> schemas 主链路
- Context Phase 2 策略管线（token-aware 选窗与截断、确定性 summary、序列化、trace）
- Context Phase 3 持久化短期记忆（RedisContextStore、backend factory、session TTL、reset_session / reset_conversation）
- observability 最小能力（`logging` + `log_until.py` 统一日志上报）
- `infra/` 本地运行基础设施（Dockerfile + compose）

## 未来预留（当前未实现）

- streaming 真实链路
- 多模态真实链路
- tools/function calling 真正执行链路
- structured output 真实能力
- 长期记忆平台
- RAG / retrieval / 向量数据库
- API key 安全治理与生产级配置分层（当前阶段不处理）

## 配置说明（当前阶段）

当前阶段采用单文件配置模式：

- 根目录 `.env.example` 是唯一配置文件
- 代码默认读取根目录 `.env.example`（见 `app/config.py`）
- `infra/compose.yaml` 直接读取根目录 `.env.example`
- 当前阶段不再使用 `.env`

## 运行方式

当前仅支持 HTTP 调用，不保留 CLI 入口。

### 方式一：本地直接运行（uvicorn）

```bash
uvicorn app.server:app --host 127.0.0.1 --port 8000 --reload
```

### 方式二：Docker Compose 运行（app + redis）

```bash
docker compose -f infra/compose.yaml up --build
```

停止：

```bash
docker compose -f infra/compose.yaml down
```

## 接口示例

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

调用 chat：

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_prompt": "你好",
    "provider": "openai"
  }'
```

重置会话上下文：

```bash
curl -X POST "http://127.0.0.1:8000/chat/reset" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "S_001",
    "conversation_id": "C_001"
  }'
```

## 日志与错误语义（当前阶段）

- 日志输出统一格式：`<time> <level> [<thread>] <logger> <file>:<line> event=<event> message=<json>`
- 前缀承载系统信息（时间、级别、线程、logger、文件、行号、event）
- `message=<json>` 仅承载业务字段
- 凭据字段（如 API key、Authorization）禁止输出
- 未知异常对外返回通用 500 语义，内部以 `error` 级记录 traceback

## 关键环境变量（摘录）

| 变量 | 说明 | 示例 |
| --- | --- | --- |
| `LLM_DEFAULT_PROVIDER` | 默认 provider | `openai` |
| `LLM_TIMEOUT_SECONDS` | 全局调用超时（秒） | `60` |
| `CONTEXT_STORE_BACKEND` | Context store backend | `redis` / `memory` |
| `CONTEXT_REDIS_URL` | Redis 连接地址 | `redis://redis:6379/0` |
| `CONTEXT_SESSION_TTL_SECONDS` | session TTL（秒） | `3600` |
| `CONTEXT_STORE_KEY_PREFIX` | Redis key 前缀 | `vi_ai_core_service:context` |
| `CONTEXT_ALLOW_MEMORY_FALLBACK` | Redis 不可用时是否回退内存 | `false` |
| `CONTEXT_MAX_TOKEN_BUDGET` | token-aware 选窗预算 | `1200` |
| `CONTEXT_TRUNCATION_TOKEN_BUDGET` | token-aware 截断预算 | `900` |
| `CONTEXT_SUMMARY_ENABLED` | 是否启用 deterministic summary | `true` |
| `CONTEXT_SUMMARY_MAX_CHARS` | summary 最大字符数 | `320` |
| `CONTEXT_FALLBACK_BEHAVIOR` | summary 回退策略 | `summary_then_drop_oldest` |

