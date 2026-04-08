# vi_ai_core_service

> 更新日期：2026-04-07

这是面向主流 C 端 AI 应用作品集项目的 Python AI Core 子系统。

当前重点：优先打通并稳定 LLM 主链路，优先保证结构清晰。

## 当前阶段范围

当前阶段仅验收基础设施能力与单轮非流式主链路：

已实现：
- HTTP 服务入口（`app/server.py`）
- `/health`、`/chat`、`/chat/reset` 路由
- API -> services -> context/prompts/providers -> schemas 主链路
- Context Phase 2：token-aware 选择/截断 + 确定性摘要 + reset
- observability 最小能力（标准库 `logging`、`log_until.py`、前缀+`message=<json>`）

未来预留（未实现）：
- streaming、多模态、tools/function calling、结构化输出、长期记忆/RAG/持久化 context 治理

## 运行方式（仅 HTTP）

当前仓库仅支持 HTTP 调用方式（不保留 CLI 入口）。

1. 启动服务：

```bash
uvicorn app.server:app --host 127.0.0.1 --port 8000 --reload
```

2. 健康检查：

```bash
curl http://127.0.0.1:8000/health
```

3. 调用 chat：

```bash
curl -X POST "http://127.0.0.1:8000/chat" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_prompt": "你好",
    "provider": "openai"
  }'
```

4. 重置会话上下文：

```bash
curl -X POST "http://127.0.0.1:8000/chat/reset" \\
  -H "Content-Type: application/json" \\
  -d '{
    "session_id": "S_001",
    "conversation_id": "C_001"
  }'
```

## 日志与错误规范（当前阶段）

- 日志输出统一格式：
- `<time> <level> [<thread>] <logger> <file>:<line> event=<event> message=<json>`
- 系统信息在前缀中展示（时间、级别、线程、logger、文件与行号、event）。
- `message=<json>` 仅承载业务字段（如 `request_id/session_id/conversation_id/provider/model`、状态码、耗时、payload 摘要）。
- 当前阶段日志内容策略：
- 业务 payload 当前阶段暂不脱敏，默认可输出（调试优先）。
- 凭据字段（如 API key、Authorization）必须禁止输出。
- 未知异常对外保持通用错误语义（HTTP 500: `服务器内部错误。`），内部通过 `error` 级日志记录 traceback。

## `.env` 关键开关

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `LOG_ENABLED` | 日志总开关配置（当前仅配置入 `AppConfig`，尚未接入运行时） | `true` |
| `LOG_LEVEL` | 日志级别配置（当前仅配置入 `AppConfig`，尚未接入运行时） | `INFO` |
| `LOG_FORMAT` | 日志格式配置（当前仅配置入 `AppConfig`，尚未接入运行时） | `json` |
| `LOG_API_PAYLOAD` | API payload 日志开关配置（当前仅配置入 `AppConfig`） | `true` |
| `LOG_PROVIDER_PAYLOAD` | Provider payload 日志开关配置（当前仅配置入 `AppConfig`） | `true` |
| `CONTEXT_MAX_TOKEN_BUDGET` | Context 选窗 token 预算 | `1200` |
| `CONTEXT_TRUNCATION_TOKEN_BUDGET` | Context 截断 token 预算（<= max） | `900` |
| `CONTEXT_SUMMARY_ENABLED` | 是否启用 deterministic summary | `true` |
| `CONTEXT_SUMMARY_MAX_CHARS` | summary 文本最大字符数 | `320` |
| `CONTEXT_FALLBACK_BEHAVIOR` | summary 超预算回退策略 | `summary_then_drop_oldest` |

