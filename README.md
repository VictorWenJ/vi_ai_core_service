# vi_ai_core_service

> 更新日期：2026-04-06

Python AI Core subsystem for a mainstream consumer AI application portfolio project.

Current focus: LLM full flow first, structure first.

## 当前阶段范围

当前阶段仅验收基础设施能力与单轮非流式主链路：

已实现：
- HTTP 服务入口（`app/server.py`）
- `/health`、`/chat` 路由
- API -> services -> context/prompts/providers -> schemas 主链路
- observability 最小能力（标准库 `logging`、前缀+`message=<json>`、request context、exception logging）

未来预留（未实现）：
- streaming、多模态、tools/function calling、structured output、复杂 context 治理

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
    "prompt": "你好",
    "provider": "openai"
  }'
```

## 日志与错误规范（当前阶段）

- 日志输出统一格式：
- `<time> <level> [<thread>] <logger> <file>:<line> event=<event> message=<json>`
- 系统信息在前缀中展示（时间、级别、线程、logger、文件与行号、event）。
- `message=<json>` 仅承载业务字段（如 `request_id/session_id/conversation_id/provider/model`、状态码、耗时、payload 摘要）。
- 当前阶段日志内容策略：
- 业务 payload 当前阶段暂不脱敏，默认可输出（调试优先，可通过开关控制）。
- 凭据字段（如 API key、Authorization）必须禁止输出。
- 未知异常对外保持通用错误语义（HTTP 500: `Internal server error.`），内部通过 `error` 级日志记录 traceback。

## `.env` 关键开关

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `LOG_ENABLED` | 是否启用 `info` 级结构化日志 | `true` |
| `LOG_LEVEL` | 日志级别（标准库 logging） | `INFO` |
| `LOG_FORMAT` | 日志格式（当前固定 `json`） | `json` |
| `LOG_API_PAYLOAD` | 是否输出 API 请求/响应业务 payload 详情 | `true` |
| `LOG_PROVIDER_PAYLOAD` | 是否输出 provider 请求/响应业务 payload 详情 | `true` |
