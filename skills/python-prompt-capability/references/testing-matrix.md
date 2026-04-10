# testing-matrix.md

## 1. 目的

本文件用于给 `python-prompt-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

### A. registry
- 已知模板查找
- 未知模板失败

### B. renderer
- 基础变量替换
- 渲染结果基本断言

### C. prompt service
- 默认 system prompt 可用性
- `build_messages` / `build_chat_messages`

### D. regression
- 主链路继续能够获取默认 system prompt

---

## 3. 原则

- 以确定性测试为主
- 先保护当前已落地的最小 Prompt 闭环
- 不把未落地平台能力写进现有测试完成态
