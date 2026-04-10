# testing-matrix.md

## 1. 目的

本文件用于给 `python-schema-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

### A. chat
- `/chat` request schema
- `/chat` response schema
- citations 字段存在与为空场景

### B. stream
- started / delta / completed / error / cancelled / heartbeat schema
- completed citations
- delta 无 citations

### C. cancel / reset
- cancel contract
- reset contract

### D. lifecycle / citation
- lifecycle 字段一致性
- citation 结构完整性
- citation 不是内部对象透传

### E. regression
- 现有主链路 contract 未被破坏
- 同步与流式表达保持兼容

---

## 3. 原则

- 以确定性测试为主
- 重点验证 contract 稳定性与兼容性
- 不让 schemas 演化为各模块临时拼字段的出口