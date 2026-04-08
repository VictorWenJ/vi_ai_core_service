# Observability 测试矩阵

> 更新日期：2026-04-07

## 当前阶段建议必测项

1. `log_report()` 基础可调用性
2. 输出前缀包含 `<file>:<line>`
3. `message=<json>` 可解析
4. dataclass/pydantic/dict/list 输入可正确序列化
5. 非 dict 输入被包装为 `{"value": ...}`

## 当前阶段暂不纳入必测项

1. request context 注入与清理
2. middleware 请求起止日志
3. `.env.example` 运行时日志开关行为
4. tracing/metrics/alerting/APM 平台能力
