# capability-scope.md

## 1. 目的

本文件用于说明 `python-llm-provider-capability` 当前阶段的能力范围，避免 skill 在执行过程中发生边界漂移。

---

## 2. 当前能力范围

当前能力范围限定为：

- chat completion provider
- stream completion provider
- embedding provider
- canonical response / chunk
- provider config / registry / factory
- provider 错误映射
- provider 相关测试

---

## 3. 当前不在范围内

当前不在范围内的能力包括：

- API 路由
- chat 主链路编排
- context state 管理
- retrieval / chunking / index
- citation 生成
- request assembly
- 长期记忆平台
- 审批流
- Case Workspace

---

## 4. 当前默认技术基线

- provider 抽象优先
- canonical contract 优先
- 流式与非流式统一治理
- embedding 纳入同一 provider 技能域
- 当前只要求文本 embedding

---

## 5. 使用原则

如果某项需求超出本文件定义的能力范围，应先更新根文档与模块 AGENTS，再更新 skill，不得在实现阶段直接越界扩展。