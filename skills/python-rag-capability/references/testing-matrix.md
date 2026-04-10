# testing-matrix.md

## 1. 目的

本文件用于给 `python-rag-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

### A. ingestion
- parser 输入输出测试
- cleaner 测试
- chunking 稳定性测试
- metadata 继承测试

### B. embedding
- 单条文本 embedding
- 批量文本 embedding
- 错误映射
- timeout 行为

### C. index
- upsert
- query
- empty index query
- dimension mismatch 保护（如实现）

### D. retrieval
- top-k 正确
- filter 正确
- 无命中结果
- retrieval 失败降级

### E. citation
- citation 格式化
- citation 字段完整性
- citation 来源可追溯性

### F. integration
- `/chat` 返回 citations
- `/chat_stream` completed 返回 citations
- delta 阶段不返回 citations
- retrieval 关闭时主链路不受影响

---

## 3. 原则

- 主回归不依赖真实外部服务
- 优先 fake / in-memory
- 集成测试可补充真实依赖，但不替代主测试矩阵