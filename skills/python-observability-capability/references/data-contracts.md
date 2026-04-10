# data-contracts.md

## 1. 目的

本文件用于说明 `app/observability/` 当前日志载荷的最小契约要求。

---

## 2. 基础载荷契约

`log_report(event, message)` 当前必须满足：

- `event` 为稳定字符串
- `message` 可被归一化为 JSON-safe 结构

---

## 3. 归一化契约

当前应支持：

- pydantic `model_dump`
- `dict`
- dataclass
- `list` / `tuple` / `set`
- 基础类型
- 未知对象退化为字符串

---

## 4. 原则

- 不直接记录不可序列化复杂运行时对象
- retrieval / citation 字段必须与代码实现同步
- 契约变更必须同步补测试
