# Observability Capability Checklist

## 目录与落位

- observability 相关代码与文档位于 `app/observability/` 与 `skills/python-observability-capability/`。
- 没有把 observability 逻辑散落到 `utils.py` / `common.py` 或无边界脚本中。
- 模块命名与文件命名体现可观测性职责。

## logging 基础设施

- 使用 Python 标准库 `logging`。
- logging 初始化入口清晰。
- 日志等级语义清晰（`info` 普通事件、`error` 异常事件）。
- `.env` true/false 开关策略清晰。

## request context

- request context 字段集合定义清晰（如 `request_id`、`session_id`、`conversation_id`、`provider`、`model`）。
- 关键链路日志能够携带上下文字段。
- 上下文字段未与业务流程耦合。

## 边界日志

- startup 配置摘要日志策略清晰。
- API 请求/响应日志策略清晰。
- service 主链路摘要日志策略清晰。
- provider 调用摘要日志策略清晰。
- exception logging 策略清晰。

## 安全性

- 不默认输出 API key / Authorization / 敏感凭据。
- 不默认输出完整敏感 payload。
- 错误日志保留定位信息但避免泄漏内部敏感细节。

## 当前阶段约束

- 未引入 tracing 平台。
- 未引入 metrics 平台。
- 未引入 alerting/APM 平台。
- 未把 observability 做成万能工具层。

## 验证与测试

- 有最小验证路径（后续实现阶段）。
- 边界日志行为可被验证（后续实现阶段）。
- 改动后完成文档回写一致性检查。
