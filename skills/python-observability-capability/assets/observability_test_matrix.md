# Observability Test Matrix

> 更新日期：2026-04-06

## 当前阶段必测项

1. logging 初始化与格式输出
2. `message=<json>` 结构可解析
3. `.env` 开关行为（`LOG_ENABLED` / `LOG_API_PAYLOAD` / `LOG_PROVIDER_PAYLOAD`）
4. request context 设置/更新/清理
5. middleware 请求起止日志与 request_id 回传
6. exception logging 保留 traceback

## 当前阶段不测项（仅预留）

1. tracing/metrics/alerting/APM 平台集成
2. 分布式追踪上下文传播

