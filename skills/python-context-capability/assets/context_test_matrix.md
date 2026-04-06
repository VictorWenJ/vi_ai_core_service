# Context Test Matrix

> 更新日期：2026-04-06

## 当前阶段必测项

1. `manager -> store` 基础调用链
2. `get_window` 空窗口读取行为
3. `append_message` 追加行为与顺序
4. 会话隔离（不同 `session_id`）
5. 基础日志事件（get/append）可观察

## 当前阶段不测项（仅预留）

1. 持久化存储（Redis/DB）
2. token-aware 裁剪
3. summary/compaction 策略

