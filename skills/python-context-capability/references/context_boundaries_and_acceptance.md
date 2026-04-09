# Context 边界与验收（Phase 4）
> 更新日期：2026-04-09

## 一、边界定义

### Context 层负责
- conversation-scoped state：`(session_id, conversation_id)`
- recent raw / rolling summary / working memory 三层短期记忆模型
- store 抽象与 backend 实现（in-memory / redis）
- manager façade（统一读写、reset、状态更新入口）
- selection / truncation / summary / serialization 策略链路
- working memory reducer 与 context block rendering

### Context 层不负责
- API 协议与路由接入
- 业务流程编排
- provider 协议适配
- prompt 资产管理
- 向量检索、RAG、长期记忆平台
- 外部 LLM 二次摘要/抽取链路

## 二、必须遵守的原则
1. 上下文主作用域必须是 `(session_id, conversation_id)`。
2. `ContextWindow.messages` 在 Phase 4 中仅表示 recent raw messages。
3. request 组装顺序由 assembler 决定，不下沉到 context 层。
4. store 私有细节（Redis key/TTL）不得泄漏到 API 或 service。
5. rolling summary 默认必须是确定性实现，可测试、可回归。
6. working memory reducer 先走规则版，宁缺毋滥。
7. reset 必须显式、作用域精确、语义可验证。

## 三、典型反模式
1. API 或 service 直接操作 Redis。
2. 用 metadata 冒充 conversation 作用域隔离。
3. 把全量历史直接塞回 `messages`，破坏分层语义。
4. 在 context 层决定最终 prompt 装配顺序。
5. 以 Phase 4 名义引入 RAG、embedding、长期记忆。
6. 引入外部 LLM 二次摘要链路导致不可控复杂度。

## 四、验收标准
1. conversation scope 隔离成立，reset 行为正确。
2. recent raw compact -> rolling summary -> 持久化链路成立。
3. working memory reducer 更新规则稳定、可测。
4. request-time 组装顺序固定且可验证。
5. in-memory / redis backend 对外契约一致。
6. trace 字段可观测 scope、分层状态与 compact 结果。
7. 主链路回归通过，未破坏非流式 chat。
8. 未越界进入长期记忆、RAG 或向量检索。

## 五、一句话总结
Phase 4 的目标是把短期上下文升级为 conversation-scoped layered short-term memory；它仍然是短期记忆工程，不是长期记忆或 RAG 平台。
