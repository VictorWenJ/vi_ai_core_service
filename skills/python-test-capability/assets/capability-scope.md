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
- retrieval / citation tests
- provider / prompt / schema 基础测试
- fake / mock / in-memory 测试支撑

---

## 3. 当前不在范围内

当前不在范围内的能力包括：

- 业务实现本身
- HTTP route 实现
- provider SDK 接入
- retrieval / chunking / embedding / index 实现
- 性能压测平台
- 混沌工程平台
- 测试替代架构设计

---

## 4. 当前默认技术基线

- 主回归优先确定性
- 同步 / 流式主链路测试并存
- Phase 6 retrieval / citation 纳入主测试面
- 外部依赖集成测试只做补充

---

## 5. 使用原则

如果某项需求超出本文件定义的能力范围，应先更新根文档与模块 AGENTS，再更新 skill，不得在实现阶段直接越界扩展。