# testing-matrix.md

## 1. 目的

本文件用于给 `python-schemas-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

### A. message
- role 校验
- content 非空校验

### B. request
- provider / model / ids 归一化
- temperature / max_tokens 校验

### C. response
- `LLMUsage` 结构
- `LLMResponse` 结构
- `to_dict()` 行为

### D. stream
- `LLMStreamChunk` 字段语义
- done / finish_reason / usage 组合语义

### E. regression
- service / provider / request assembler 对 `LLM*` 契约的兼容性

---

## 3. 原则

- 以确定性测试为主
- 先保护当前已落地的内部 canonical contract
- 不把未落地 API / citation 模型写进测试完成态
