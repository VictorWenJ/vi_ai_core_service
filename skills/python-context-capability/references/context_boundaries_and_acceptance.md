# Context 层边界与验收标准

> 更新日期：2026-04-08

## 一、边界定义

### Context 层负责什么

- 会话历史 canonical model（message/window/策略中间结果）
- store 抽象与 store adapter
- `ContextManager` façade（get/append/reset/replace）
- token-aware selection / truncation
- deterministic summary / compaction
- history serialization 与策略 trace
- 持久化短期记忆后端、TTL、namespace 与 reset 语义

### Context 层不负责什么

- API 协议接入
- service 业务编排
- provider SDK / HTTP 调用
- prompt 模板管理与 system prompt 选择
- RAG / 检索 / 长期记忆 / 用户画像
- 多区域分布式状态系统

---

## 二、必须遵守的原则

1. Context 层必须 provider-agnostic
2. 默认策略顺序必须固定：selection -> truncation -> summary -> serialization
3. 持久化逻辑必须局限在 `app/context/stores/`
4. `ContextManager` 必须是统一 façade，不允许上层绕过
5. TTL / key prefix / namespace 必须集中配置，不得散落硬编码
6. reset 必须显式触发，并精确限定作用范围
7. token accounting 允许工程近似，但必须可解释、可测试
8. Phase 3 只做 durable short-term memory，不得偷渡 RAG / 长期记忆

---

## 三、典型反模式

1. 在 `chat_service.py` 或 API 层手写 Redis 逻辑
2. 在多个文件里重复拼接 Redis key 或 TTL
3. 把持久化短期记忆直接包装成“长期 memory”
4. 在 context 层直接接入外部 LLM 做摘要
5. 为了 persistence 破坏 Phase 2 默认 policy pipeline
6. reset 行为跨 session / conversation 误删数据
7. `ContextPolicyConfig` 与持久化配置职责混写
8. 只有内存实现，没有为 Redis / fallback 行为补测试

---

## 四、Phase 3 验收标准

一个合格的 Phase 3 结果至少满足：

1. 默认 token-aware 主链路保持稳定运行
2. `RedisContextStore`（或等价持久化 store）已接入
3. request-time 能从持久化 store 读取 session history
4. response-time 能写回 user / assistant 历史
5. session TTL / namespace / reset 语义清晰、可测试
6. `reset_session` 与 `reset_conversation` 行为正确
7. `InMemoryContextStore` 仍可作为 dev/test fallback
8. 文档、skill、代码、测试四者一致
9. 未越界进入长期记忆、RAG 或语义检索

---

## 五、一句话总结

Context Phase 3 的目标是：  
在保持 Phase 2 token-aware 上下文治理主链路稳定的前提下，把短期会话 history 升级为**可持久化、可恢复、可生命周期管理的 session memory**，但仍然不进入长期记忆或检索增强阶段。
