# tests/AGENTS.md

> 更新日期：2026-04-10

## 1. 文档定位

本文件定义 `tests/` 的职责、边界、结构约束与 review 标准。  
当前阶段，本文件临时同时承担该模块的 AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW 职责。

---

## 2. 模块定位

`tests/` 是项目级回归保护层。  
它用于保证同步 chat、流式 chat、上下文工程、知识检索与引用等关键能力在项目演进中保持稳定。

---

## 3. 当前阶段职责

当前阶段除保持已有测试外，必须新增对 Phase 6 的最小回归保护。

---

## 4. Phase 6 测试重点

### 4.1 ingestion pipeline
- parser 解析正确
- cleaner 行为稳定（如实现）
- chunker 切块稳定
- chunk metadata 继承正确

### 4.2 embedding / index
- embedding provider 返回结构正确
- index upsert 正确
- index query 正确
- in-memory index 行为稳定

### 4.3 retrieval service
- top-k 正确
- filter 正确
- 空结果正确
- retrieval 失败可降级

### 4.4 request assembly
- retrieved knowledge block 被正确插入
- 顺序为：
  - system
  - working memory
  - rolling summary
  - retrieved knowledge
  - recent raw
  - user

### 4.5 同步响应
- `/chat` 返回 citations
- citation 数量、字段、结构稳定

### 4.6 流式响应
- `/chat_stream` completed 事件带 citations
- delta 阶段不带 citations
- completed / cancelled / failed 不混淆

### 4.7 兼容性
- Phase 4 / Phase 5 既有测试不被破坏
- retrieval 关闭时主链路仍可运行

---

## 5. 测试风格要求

1. 优先做稳定、确定性的测试
2. 不依赖真实外部 embedding / vector 服务做主回归
3. 使用 fake / in-memory 实现保障测试稳定
4. 对外部依赖集成测试可以做补充，但不能替代主回归

---

## 6. 修改规则

1. 不允许只测 happy path
2. 不允许 Phase 6 改动却不补 retrieval / citation 测试
3. 不允许把所有测试都绑定真实 Qdrant 或真实外部 embedding 服务
4. 不允许不验证 request assembly 顺序
5. 不允许不验证同步与流式两条链路的 citation 输出差异

---

## 7. Code Review 清单

1. 是否新增了 ingestion / retrieval / citation 相关测试？
2. request assembly 的 knowledge block 顺序是否有测试保护？
3. `/chat` 与 `/chat_stream` 的 citation 行为是否都有测试？
4. retrieval 失败 / 空结果 / 降级路径是否有测试？
5. 是否没有破坏 Phase 4 / Phase 5 既有测试面？

---

## 8. 一句话总结

`tests/` 在 Phase 6 中的重点，是为 ingest、retrieval、citation、knowledge-aware request assembly 以及同步/流式两条链路新增最小而稳定的回归保护，同时不破坏 Phase 4 / Phase 5 既有测试体系。