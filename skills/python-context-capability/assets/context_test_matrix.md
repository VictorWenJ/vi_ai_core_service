# Context 测试矩阵
> 更新日期：2026-04-09

## 当前阶段必测项（Phase 4）

### A. 作用域与生命周期
1. 同一 `session_id` 下不同 `conversation_id` 不串数据
2. `reset_conversation` 仅清理目标 conversation scope
3. `reset_session` 清理目标 session 下所有 conversation scope
4. 无 `conversation_id` 时默认 scope 行为一致

### B. 策略链路与分层语义
1. token-aware window selection 在不同预算下行为稳定
2. token-aware truncation 对超长消息可控截断
3. deterministic summary 行为稳定且可预测
4. `ContextWindow.messages` 仅承载 recent raw，不再承载全量历史
5. recent raw 超预算触发 compact，保留最近消息

### C. Rolling Summary
1. compact 产生的旧片段进入 rolling summary
2. rolling summary 可持续 merge，`source_message_count` 正确累积
3. rolling summary 超长度时按规则裁剪
4. rolling summary 编解码后结构不丢失

### D. Working Memory Reducer
1. `active_goal/constraints/decisions/open_questions/next_step` 更新规则正确
2. 去重、限项、限长生效
3. 空输入不污染已有状态
4. 变更时间戳仅在状态变化时更新

### E. Request Assembler（读链路）
1. 有 session 时加载服务端上下文；无 session 时不加载
2. 组装顺序严格为：`system -> working_memory -> rolling_summary -> recent_raw -> user`
3. 缺省层（working memory / rolling summary）为空时可优雅跳过
4. `context_assembly` trace 字段完整、语义清晰

### F. Chat Service（写链路）
1. 响应后 recent raw 写回成功
2. 写回触发 compaction 时 runtime_meta 正确
3. rolling summary 与 working memory 写回成功
4. `/chat/reset` 通过 service->manager->store 路径执行

### G. Store Backend 一致性
1. In-memory / Redis 在 get/append/replace/reset 语义一致
2. Redis conversation key schema 与 session 索引行为正确
3. Redis TTL 写入刷新生效
4. 跨实例重建后可恢复未过期上下文

## 回归必测项
1. `/chat` 非流式主链路稳定
2. provider 调用主链路未被 context 升级破坏
3. prompt 组装基础行为稳定
4. 配置加载与 backend factory 行为稳定

## 当前阶段不测项（仅预留）
1. embedding / 向量检索 / RAG
2. 长期记忆与跨会话画像
3. 外部 LLM 二次摘要 worker
4. 多模态与 streaming 真实链路
