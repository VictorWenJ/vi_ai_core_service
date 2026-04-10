# testing-matrix.md

## 1. 目的

本文件用于给 `python-llm-provider-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

### A. chat
- 基础 completion
- provider 错误映射
- usage / finish_reason 映射

### B. stream
- chunk 序列稳定
- canonical stream chunk 结构
- error 路径
- finish 路径

### C. embedding
- 单条文本 embedding
- 批量文本 embedding
- 维度与数据类型稳定性
- timeout / error 行为

### D. config / registry
- provider config 加载
- registry / factory 选择
- 不同 provider 初始化行为

### E. regression
- 同步主链路未被 provider 改动破坏
- 流式主链路未被 provider 改动破坏
- rag 对 embedding 的接入需求未被破坏

---

## 3. 原则

- 以确定性测试为主
- 优先验证 canonical contract、错误映射与 embedding 稳定性
- 不让厂商差异扩散到上层模块