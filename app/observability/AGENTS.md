# app/observability/AGENTS.md

> 更新日期：2026-04-07

## 1. 文档定位

本文件定义 `app/observability/` 的模块职责、边界、审查标准与交付门禁。  
本文件只约束 observability 模块本身，不替代根目录治理文档。

---

## 2. 模块定位

`app/observability/` 是当前阶段的横切日志基础设施层。  
当前代码现实是最小实现：统一日志上报函数 `log_report()`。

当前目录核心文件：

- `log_until.py`：统一日志上报与标准化输出
- `__init__.py`：导出 `log_report`

---

## 3. 本层职责

当前阶段本层负责：

1. 提供统一日志上报入口（`log_report(event, message)`）
2. 固化日志输出格式：
`<time> <level> [<thread>] <logger> <file>:<line> event=<event> message=<json>`
3. 统一把业务信息放在 `message=<json>` 中
4. 将 dataclass/pydantic/dict/list 等对象尽量归一化为 JSON 可序列化结构
5. 为 API / services / providers 提供统一日志调用方式

---

## 4. 本层不负责什么

当前阶段本层不负责：

1. request context 管理与透传
2. middleware 级请求日志
3. 统一异常日志封装中间层
4. tracing / metrics / alerting / APM 平台
5. 业务流程编排与 provider 接入逻辑
6. 退化为万能 `utils/common` 杂项层

---

## 5. 依赖边界

### 允许依赖

- Python 标准库（`logging/json/sys/dataclasses`）

### 禁止依赖

- `app/api`、`app/services`、`app/providers` 的业务流程实现
- `app/prompts`、`app/context` 的业务逻辑

说明：

- 业务层可以调用 observability。
- observability 不反向依赖业务层。

---

## 6. 当前实现事实（必须与代码一致）

1. 当前仅保留 `log_until.py` 一套实现。
2. 运行时日志级别当前固定为 `INFO`（由 `log_until.py` 内部设置）。
3. `AppConfig` 中 `LOG_*` 配置项目前仅完成配置读取，尚未接入 `log_until.py` 运行时行为。
4. 当前未实现 request context 注入与清理流程。
5. 当前未实现独立 middleware/request_id 自动透传。

---

## 7. 设计原则

1. 统一入口：日志必须优先走 `log_report`。
2. 输出可定位：必须保留 `<file>:<line>`，便于排查。
3. 结构化优先：业务信息放 `message=<json>`，避免不可解析拼接字符串。
4. 安全优先：禁止输出 API key、Authorization 等凭据字段。
5. 小步演进：后续若恢复 context/middleware/开关接入，必须先文档后代码。

---

## 8. 当前阶段能力声明

- 已实现：
  - `log_report` 统一上报
  - 前缀 + `message=<json>` 输出
  - API/service/provider 主链路可调用日志
- 未实现（仅预留）：
  - request context 贯穿
  - middleware 自动注入 request_id
  - `.env` 运行时日志开关接入
  - tracing/metrics/alerting/APM 平台建设

---

## 9. 修改规则

修改 `app/observability/` 时必须遵守：

1. 先确认改动确属 observability 基础设施职责。
2. 不把业务编排逻辑放进 observability。
3. 不绕开统一输出格式约束。
4. 若新增功能（如 context/middleware），必须同步更新：
   - 根目录文档
   - 本模块 AGENTS
   - `skills/python-observability-capability/` 文档

---

## 10. Code Review 清单

评审 `app/observability/` 相关改动时，至少检查：

1. 是否仍使用标准库 `logging`。
2. 是否仍满足前缀 + `message=<json>` 输出格式。
3. 是否能通过 `<file>:<line>` 快速定位日志来源。
4. 是否把系统信息与业务 JSON 混写。
5. 是否输出了敏感凭据字段。
6. 是否引入了当前阶段无关的平台化能力。

---

## 11. 测试要求（当前阶段最小）

当前阶段建议至少覆盖：

1. `log_report` 输出格式可解析
2. 常见对象（dict/dataclass/pydantic）可被序列化
3. 非 dict 值会被包装为 `{"value": ...}`

注：当前仓库尚无独立 observability 测试文件，后续恢复时应补齐。

---

## 12. 禁止事项

1. 到处 `print` 替代统一日志入口
2. 在业务代码中大量手写不同日志格式
3. 输出 API key / Authorization 明文
4. 在当前阶段引入 tracing/metrics/alerting/APM 重型平台

---

## 13. 一句话总结

当前 `app/observability/` 是最小日志基础设施层，核心就是统一 `log_report` 与统一输出格式约束。

---

## 14. 本模块任务执行链路（强制）

Observability 类任务必须按以下顺序执行：

1. 根目录四文档
2. 本文件
3. `skills/python-observability-capability/` 文档
4. 代码改动
5. 自审与文档回写

标准闭环：

`根目录文档 -> app/observability/AGENTS.md -> skill -> 代码实现 -> review -> 文档回写`

---

## 15. 本模块交付门禁

1. 与当前代码事实不一致的文档描述必须先修正。
2. 涉及日志格式变更必须给出样例并完成回归验证。
3. 若宣称 `LOG_*` 开关生效，必须在代码中有真实接入实现。
