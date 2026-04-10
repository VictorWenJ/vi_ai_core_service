# acceptance-checklist.md

## 1. 目的

本文件用于在 `app/api/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### 路由
- [ ] `/chat` 可用
- [ ] `/chat_stream` 可用
- [ ] `/chat_stream_cancel` 可用
- [ ] `/chat_reset` 可用
- [ ] `/health` 可用

### 契约
- [ ] request / response schema 清晰
- [ ] SSE 事件格式稳定
- [ ] `/chat` citations 可输出
- [ ] `/chat_stream` completed citations 可输出
- [ ] delta 阶段不输出 citations

### 错误处理
- [ ] 错误已做 HTTP 映射
- [ ] 不直接向客户端泄漏底层异常细节
- [ ] retrieval 失败可配合 service 做降级

### 边界
- [ ] API 仍为薄路由
- [ ] 未混入 retrieval / context / provider 逻辑
- [ ] 未直接访问底层向量库或 embedding SDK

### 回归
- [ ] 未破坏同步 chat 主链路
- [ ] 未破坏流式 chat 主链路
- [ ] 未破坏 cancel / reset 行为

### 文档治理
- [ ] 改动符合模块 AGENTS
- [ ] 改动符合本 skill
- [ ] 未无故改变其他文件风格