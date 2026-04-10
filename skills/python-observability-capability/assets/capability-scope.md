# capability-scope.md

## 1. 目的

本文件用于说明 `python-observability-capability` 当前阶段的能力范围，避免 skill 在执行过程中发生边界漂移。

---

## 2. 当前能力范围

当前能力范围限定为：

- `log_report`
- JSON-safe 序列化
- request / stream / context assembly / provider 相关日志
- retrieval / citation 生命周期相关日志
- observability 相关测试

---

## 3. 当前不在范围内

当前不在范围内的能力包括：

- chat 主链路编排
- retrieval / chunking / embedding / index
- citation 生成
- tracing / metrics / alerting 平台
- 审批流
- Case Workspace

---

## 4. 当前默认技术基线

- 结构化日志
- JSON-safe
- stdout logger
- 当前包含 retrieval / citation 专项字段

---

## 5. 使用原则

如果某项需求超出本文件定义的能力范围，应先更新根文档与模块 AGENTS，再更新 skill，不得在实现阶段直接越界扩展。
