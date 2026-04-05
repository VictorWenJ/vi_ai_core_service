# vi_ai_core_service

Python AI Core subsystem for a mainstream consumer AI application portfolio project.

Current focus: LLM full flow first, structure first.

## 运行方式

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
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "你好",
    "provider": "openai"
  }'
```
