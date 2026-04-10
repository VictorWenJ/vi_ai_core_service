# capability-scope.md

## 1. 目的

本文件用于说明 `python-test-capability` 当前阶段的能力范围，避免 skill 在执行过程中发生边界漂移。

---

## 2. 当前能力范围

当前能力范围限定为：

- unit tests
- integration tests
- API contract tests
- lifecycle tests
- request assembly tests
- provider / prompt / config tests
- rag ingestion / retrieval / citation / degrade tests

---

## 3. 当前不在范围内

当前不在范围内的能力包括：

- 业务实现本身
- retrieval / chunking / embedding / index 实现
- 用测试替代文档治理
- 性能压测平台
- 混沌工程平台

---

## 4. 当前默认技术基线

- 保护已落地的 Phase 2~6 主链路
- 主回归优先 fake / in-memory
- 包含 retrieval / citation 测试面

---

## 5. 使用原则

如果某项需求超出本文件定义的能力范围，应先更新根文档与模块 AGENTS，再更新 skill，不得在实现阶段直接越界扩展。
