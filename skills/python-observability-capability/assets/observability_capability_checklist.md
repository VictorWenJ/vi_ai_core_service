# Observability Capability Checklist

> 更新日期：2026-04-07

## 目录与落位

- observability 代码集中在 `app/observability/`。
- 当前阶段核心文件是 `log_until.py` 与 `__init__.py`。
- 没有把日志逻辑散落到 `utils.py` / `common.py`。

## 日志格式

- 使用 Python 标准库 `logging`。
- 前缀遵守：`<time> <level> [<thread>] <logger> <file>:<line> event=<event>`。
- 正文遵守：`message=<json>`。
- 系统信息不混入业务 JSON。

## 日志上报入口

- 业务层统一调用 `log_report(event, message)`。
- 常见对象（dict/dataclass/pydantic/list）可被 JSON 化。
- 非 dict 值会被包装成 `{"value": ...}`。

## 安全性

- 不输出 API key、Authorization 等凭据字段。
- 业务 payload 若包含敏感字段，调用方需显式收敛。

## 阶段约束

- 未引入 tracing/metrics/alerting/APM 平台。
- 未宣称 request context/middleware 已落地（除非代码真实实现）。
- 未宣称 `LOG_*` 开关已生效（除非代码真实接入）。

## 验证与回写

- 至少执行最小导入或测试验证。
- 文档与代码事实保持一致。
- 改动后完成根文档/模块文档/skill 回写检查。
