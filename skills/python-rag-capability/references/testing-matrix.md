# testing-matrix.md

## 1. 目的

本文件用于给 `python-rag-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

当前代码基线中，本模块已有运行时代码。
后续改动按以下矩阵补齐：

### A. models
- knowledge models 初始化
- metadata 继承与字段稳定性

### B. ingest
- parser
- chunker
- chunk metadata

### C. retrieval
- index upsert / query
- top-k
- metadata filter

### D. citation
- citation 格式化
- citation 来源追溯

### E. robustness
- retrieval 失败降级
- 不拖垮主 chat 链路

---

## 3. 原则

- 先有运行时代码，再有模块内测试矩阵
- 以确定性测试为主
- 不把未落地能力写进现有测试完成态
