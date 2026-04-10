# testing-matrix.md

## 1. 目的

本文件用于给 `python-api-capability` 提供标准测试矩阵参考。

---

## 2. 测试矩阵

### A. chat
- `/chat` 正常响应
- `/chat` citations 输出
- `/chat` 错误映射

### B. stream
- `/chat_stream` 返回 `text/event-stream`
- started / delta / completed 顺序
- completed citations 输出
- delta 无 citations
- error / cancelled 路径

### C. cancel
- `/chat_stream_cancel` 命中有效流
- `/chat_stream_cancel` 命中无效流
- cancel 响应契约正确

### D. reset
- `/chat_reset` 重置整个 session
- `/chat_reset` 重置 conversation
- reset 响应契约正确

### E. health
- `/health` 可用
- 基础返回结构正确

### F. integration
- API 与 service 协作正常
- retrieval 失败时 API 行为可控
- 同步与流式主链路未被 Phase 6 改动破坏

---

## 3. 原则

- API 主回归以 HTTP / 集成测试为主
- 不把底层 provider / retrieval 真实外部依赖作为主回归前置
- 重点验证契约、边界、协议与降级行为