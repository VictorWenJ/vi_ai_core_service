# acceptance-checklist.md

## 1. 目的

本文件用于在 `tests/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### 主链路
- [ ] `/chat` 路径已覆盖
- [ ] `/chat_stream` 路径已覆盖
- [ ] cancel / reset 路径已覆盖

### 关键差异
- [ ] completed / failed / cancelled 差异已覆盖
- [ ] request assembly 顺序与过滤已覆盖

### 基础模块
- [ ] provider / prompt / API / config 相关回归面已覆盖
- [ ] rag / citation / degrade 相关回归面已覆盖

### 边界
- [ ] 未把未落地能力写成已覆盖事实
- [ ] 未过度依赖真实外部服务

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格
