# SKILL.md

> skill_name: python-api-capability  
> module_scope: app/api/  
> status: active  
> last_updated: 2026-04-10

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `app/api/` 模块中进行 HTTP / SSE 接入层的设计、实现、测试与增量演进。

本 skill 的目标不是生成“泛化的 FastAPI 示例代码”，而是约束在本项目文档治理体系下，按企业级 AI 应用的标准实现同步聊天、流式聊天、取消、重置与健康检查等 API 接入能力。

---

## 2. Skill 适用范围

本 skill 适用于以下类型的工作：

1. `/chat` 路由设计与实现
2. `/chat_stream` SSE 路由设计与实现
3. `/chat_stream_cancel` 路由设计与实现
4. `/chat_reset` 路由设计与实现
5. `/health` 相关接口
6. API 层 request / response schema
7. SSE 事件格式化辅助
8. API 错误映射与 HTTPException 映射
9. API 层测试与 HTTP 集成测试

---

## 3. Skill 不适用范围

本 skill 不用于以下工作：

1. chat 主链路编排
2. assistant message lifecycle 状态机实现
3. context memory 实现
4. retrieval / chunking / embedding / index 实现
5. provider SDK 调用实现
6. citation 生成逻辑
7. 长期记忆平台
8. 审批流
9. Case Workspace

如任务超出上述边界，应转交对应模块 skill 处理。

---

## 4. 本 skill 的核心原则

### 4.1 API 只做接入与协议输出
API 层负责：
- 收请求
- 校验
- 调 service
- 返回 JSON
- 返回 SSE

不负责业务状态机和内部编排。

### 4.2 SSE 是协议，不是业务状态机
`/chat_stream` 的职责是：
- 建立 `text/event-stream`
- 将 canonical stream event 输出为标准 SSE 文本

不负责定义业务生命周期，也不负责 provider chunk 归一化。

### 4.3 外部契约必须稳定
- `/chat`
- `/chat_stream`
- `/chat_stream_cancel`
- `/chat_reset`

都必须有清晰、稳定、可测试的数据契约。

### 4.4 citation 是对外输出能力，不是内部实现细节
Phase 6 后，API 层必须支持输出 citations，但不能泄漏：
- retrieval 内部对象
- 向量库细节
- embedding 细节
- 知识块装配细节

### 4.5 错误必须映射为清晰 HTTP 语义
API 层必须负责将 service / provider 层错误转换成可理解的 HTTP 错误响应，而不是直接将底层异常透传给客户端。

---

## 5. 默认阶段基线

当前 skill 默认基线如下：

- API 框架：FastAPI
- 流式协议：SSE
- `/chat_stream` 返回 `text/event-stream`
- `/chat_stream_cancel` 负责显式取消语义
- `/chat_reset` 负责上下文重置入口
- `/chat` 返回 citations
- `/chat_stream` 仅在 completed 事件返回 citations

如需变更该基线，必须先更新根目录文档与模块 AGENTS，再进入实现。

---

## 6. 标准执行流程

执行 `app/api/` 相关任务时，必须遵循以下顺序：

1. 阅读根目录文档  
   - `AGENTS.md`
   - `PROJECT_PLAN.md`
   - `ARCHITECTURE.md`
   - `CODE_REVIEW.md`

2. 阅读模块文档  
   - `app/api/AGENTS.md`

3. 阅读本 skill  
   - `skills/python-api-capability/SKILL.md`

4. 按需阅读 assets / references  
   - `assets/capability-scope.md`
   - `assets/delivery-workflow.md`
   - `assets/acceptance-checklist.md`
   - `references/module-boundaries.md`
   - `references/data-contracts.md`
   - `references/testing-matrix.md`

5. 明确本轮任务边界  
6. 设计最小增量改动  
7. 补充测试  
8. 自检与回归验证

---

## 7. 标准交付物要求

API 相关任务，至少应交付以下之一或多项：

1. 路由实现更新
2. API schema 更新
3. SSE 序列化辅助更新
4. API 错误映射更新
5. cancel/reset 入口更新
6. API 层测试更新

仅给概念说明、不落代码、不补测试，不视为完成。

---

## 8. 实现约束

### 8.1 薄路由约束
API 层必须保持薄路由。  
不得把 business orchestration 写进 route handler。

### 8.2 SSE 约束
- SSE 文本格式化留在 API 层
- event name 必须稳定
- payload 必须来自 service 已归一化结果
- delta 阶段不输出 citations

### 8.3 cancel / reset 约束
- `/chat_stream_cancel` 只负责接入与转发取消请求
- `/chat_reset` 只负责接入与转发上下文重置请求
- API 不承担取消注册表和上下文重置的内部实现

### 8.4 错误映射约束
- API 必须将底层异常映射为稳定 HTTP 语义
- 不直接把 provider / service traceback 暴露给客户端
- 服务端日志可保留调试信息，但响应体必须可控

### 8.5 citations 约束
- `/chat` 输出 citations
- `/chat_stream` 仅 completed 输出 citations
- citation 必须来自 service 给出的结构化结果，不允许 API 自行拼装业务语义

---

## 9. 与其他模块的协作约束

### 与 services 协作
`services` 负责 chat / stream / cancel / reset 的业务编排；`api` 负责接入与返回。  
`api` 不替代 `services`。

### 与 schemas 协作
API 层的 request / response / event 必须通过 schema 表达。  
不得无 schema 增加临时字段。

### 与 context 协作
API 层不直接访问 context manager。  
重置、状态变化都应经由 service 暴露。

### 与 rag 协作
API 层不直接访问 retrieval / index / embedding。  
citations 只是输出结果，不是 API 层内部逻辑。

---

## 10. 测试要求

API 相关实现至少补以下测试之一或多项：

1. `/chat` 正常响应测试
2. `/chat_stream` SSE 响应测试
3. `/chat_stream_cancel` 测试
4. `/chat_reset` 测试
5. `/health` 测试
6. citations 输出测试
7. retrieval 失败时 API 降级测试
8. HTTP 集成测试

---

## 11. Review 要点

提交前至少自查：

1. API 是否仍保持薄路由？
2. 是否没有把 retrieval / context / provider 逻辑混入 API 层？
3. `/chat` 是否可稳定返回 citations？
4. `/chat_stream` 是否仅在 completed 返回 citations？
5. `/chat_stream_cancel` 与 `/chat_reset` 是否职责清晰？
6. 错误映射是否稳定？
7. 是否补了测试？
8. 是否破坏了现有同步或流式主链路？

---

## 12. 关联文件

- `assets/capability-scope.md`
- `assets/delivery-workflow.md`
- `assets/acceptance-checklist.md`
- `references/module-boundaries.md`
- `references/data-contracts.md`
- `references/testing-matrix.md`

---

## 13. 一句话总结

本 skill 的目标，是确保 `app/api/` 在当前项目中以企业级、可增量演进、可测试、可审查的方式落地同步与流式 API 接入能力，并在 Phase 6 中稳定承接 citations、cancel、reset 与 SSE 协议输出，而不是演化成承担业务编排职责的厚路由层。