# testing-matrix.md

## 1. 目的

本文件用于给 `python-context-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

### A. models
- context model 初始化
- lifecycle 字段完整性
- default value 安全性

### B. stores
- in-memory store
- redis store
- codec 序列化 / 反序列化
- scope 隔离

### C. manager
- placeholder 创建
- completed finalize
- failed / cancelled 收口
- reset_session / reset_conversation

### D. layered memory
- recent raw 更新
- rolling summary 更新
- working memory 更新
- only completed 进入标准 memory update

### E. request assembly support
- non-completed assistant message 过滤
- completed assistant message 正常参与装配

### F. compatibility
- retrieval 引入后 context 行为不变
- 流式主链路下 completed / failed / cancelled 行为稳定

---

## 3. 原则

- 主回归应尽量使用确定性测试
- store 语义要跨实现保持稳定
- 重点验证 lifecycle、scope、layered memory 和 compatibility