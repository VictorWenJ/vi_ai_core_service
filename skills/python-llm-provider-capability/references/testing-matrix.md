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

### C. config / registry
- provider config 加载
- registry / maturity 选择
- implemented / scaffolded 行为

### D. regression
- 同步主链路未被 provider 改动破坏
- 流式主链路未被 provider 改动破坏

---

## 3. 原则

- 以确定性测试为主
- 优先验证 canonical contract、错误映射与 registry 稳定性
- 不把未落地 embedding 能力写进现有测试完成态
