# Observability Capability Checklist

> 更新日期：2026-04-06


## 目录与落位

- observability 相关代码与文档位于 `app/observability/` 与 `skills/python-observability-capability/`。
- 没有把 observability 逻辑散落到 `utils.py` / `common.py` 或无边界脚本中。
- 模块命名与文件命名体现可观测性职责。

## logging 基础设施

- 使用 Python 标准库 `logging`。
- logging 初始化入口清晰。
- 控制台前缀遵守：`<time> <level> [<thread>] <logger> <file>:<line> event=<event>`。
- 日志正文遵守：`message=<json>`。
- 日志等级语义清晰（`info` 普通事件、`error` 异常事件）。
- `.env` true/false 开关策略清晰。

## request context

- request context 字段集合定义清晰（如 `request_id`、`session_id`、`conversation_id`、`provider`、`model`）。
- 关键链路日志能将上下文字段写入 `message` JSON。
- 上下文字段未与业务流程耦合。

## 边界日志

- startup 配置摘要日志策略清晰。
- API 请求/响应日志策略清晰。
- service 主链路摘要日志策略清晰。
- provider 调用摘要日志策略清晰。
- exception logging 策略清晰。
- `method/path` 等系统信息不进入 `message` JSON。

## 安全性

- API key / Authorization / 敏感凭据必须禁止输出。
- 当前阶段业务 payload 默认可输出，并由 `LOG_API_PAYLOAD` / `LOG_PROVIDER_PAYLOAD` 控制。
- 错误日志保留定位信息与 traceback，同时不输出凭据字段。

## 当前阶段约束

- 未引入 tracing 平台。
- 未引入 metrics 平台。
- 未引入 alerting/APM 平台。
- 未把 observability 做成万能工具层。

## 验证与测试

- 有最小验证路径（当前阶段）。
- 边界日志行为可被验证（当前阶段）。
- `<file>:<line>` 定位字段可验证且指向真实调用点。
- 改动后完成文档回写一致性检查。
