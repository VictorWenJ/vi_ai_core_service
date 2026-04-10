# acceptance-checklist.md

## 1. 目的

本文件用于在 `tests/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### 主链路
- [ ] `/chat` 有测试保护
- [ ] `/chat_stream` 有测试保护
- [ ] cancel / reset 有测试保护

### 生命周期
- [ ] completed / failed / cancelled 有区别性测试
- [ ] only completed 进入标准 memory update 有测试保护

### retrieval / citation
- [ ] `/chat` citations 有测试保护
- [ ] `/chat_stream` completed citations 有测试保护
- [ ] delta 无 citations 有测试保护
- [ ] retrieval 失败降级有测试保护

### 基础模块
- [ ] provider canonical contract 有测试
- [ ] prompt registry / renderer 有测试
- [ ] schema contract 有测试
- [ ] context lifecycle 有测试

### 质量
- [ ] 测试优先确定性
- [ ] 没有过度依赖真实外部服务
- [ ] 测试可读、可维护

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格