# testing-matrix.md

## 1. 目的

本文件用于给 `python-observability-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

### A. serialization
- pydantic / dict / dataclass / list 归一化
- 未知对象字符串化

### B. logger
- `log_report` 输出稳定
- stdout logger 初始化稳定

### C. robustness
- 不可序列化输入不崩溃
- 流式场景不崩溃

### D. future Phase 6
- 若后续新增 retrieval / citation 观测，再补对应测试

---

## 3. 原则

- 以确定性测试为主
- 先保护当前已落地的结构化日志能力
- 不把未落地字段写进现有测试完成态
