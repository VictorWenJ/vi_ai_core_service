# Observability 边界与验收标准

> 更新日期：2026-04-07

## 一、当前代码事实

当前仓库 observability 最小实现为：

- `app/observability/log_until.py`
- `app/observability/__init__.py`（仅导出 `log_report`）

核心能力：

1. 统一日志上报函数 `log_report(event, message)`
2. 统一输出格式（前缀 + `message=<json>`）
3. 通用对象 JSON 化

---

## 二、边界定义

### 当前负责

1. 日志输出格式统一
2. 日志调用入口统一
3. 日志可定位性（文件与行号）

### 当前不负责

1. request context 贯穿
2. middleware 自动日志
3. `.env.example` 运行时日志开关接入
4. tracing/metrics/alerting/APM 平台

---

## 三、必须遵守的原则

1. 使用标准库 `logging`。
2. 前缀字段与业务 JSON 分离。
3. 系统信息在前缀，不写入业务 JSON。
4. 禁止输出凭据字段。
5. 不将 observability 做成万能工具层。

---

## 四、典型反模式

1. 到处 `print`，不走统一 `log_report`
2. 业务 JSON 里混入系统字段（method/path/thread 等）
3. 输出 API key/Authorization
4. 文档宣称开关已生效，但代码未接入
5. 当前阶段提前引入 tracing/metrics/alerting 平台

---

## 五、验收标准

一个合格改动至少满足：

1. 目录与职责落位正确
2. 日志格式保持稳定
3. `message=<json>` 可解析且业务字段清晰
4. `<file>:<line>` 可定位
5. 文档与代码事实一致

---

## 六、一句话总结

当前 observability 的核心是“统一日志上报与输出格式”，不是“构建观测平台”。
