# testing-matrix.md

## 1. 目的

本文件用于给 `python-observability-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

### A. serialization
- JSON-safe serialization
- dataclass projection
- non-serializable object protection

### B. request tracing
- request_id / session_id / conversation_id 输出
- provider / model 字段输出
- status / latency 输出

### C. stream tracing
- assistant_message_id 输出
- event count 输出
- finish / error / cancelled 字段输出
- 流式链路不因日志失败而中断

### D. retrieval tracing
- retrieval_query 输出
- retrieval_top_k 输出
- retrieval_filters 输出
- retrieved_chunk_count 输出
- citation_count 输出

### E. regression
- 同步主链路未被 observability 改动破坏
- 流式主链路未被 observability 改动破坏

---

## 3. 原则

- 以确定性测试为主
- 重点验证安全序列化与关键字段稳定性
- 不让 observability 成为主链路脆弱点