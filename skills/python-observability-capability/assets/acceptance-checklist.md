# acceptance-checklist.md

## 1. 目的

本文件用于在 `app/observability/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### 结构化
- [ ] 日志仍为结构化输出
- [ ] 关键字段命名稳定
- [ ] request / stream / retrieval 字段可检索

### JSON-safe
- [ ] 不可序列化对象不会直接进入日志
- [ ] 深层运行时对象已投影为安全字段
- [ ] 流式场景下日志不会导致主链路崩溃

### retrieval / citation
- [ ] retrieval_query 可观测
- [ ] retrieval_top_k 可观测
- [ ] retrieval_filters 可观测
- [ ] retrieved_chunk_count 可观测
- [ ] citation_count 可观测

### 边界
- [ ] 未混入 chat / stream / retrieval 主逻辑
- [ ] 未把日志当成状态存储
- [ ] 未输出不必要敏感正文

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格