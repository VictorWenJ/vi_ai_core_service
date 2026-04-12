# SKILL.md

> skill_name: python-api-capability
> module_scope: app/api/
> status: active
> last_updated: 2026-04-10

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `app/api/` 模块中进行 HTTP / SSE 接入层的设计、实现、测试与增量演进。

本 skill 的目标不是生成“泛化的 FastAPI 示例代码”，而是约束在本项目文档治理体系下，按当前仓库真实代码结构实现：

- `/chat`
- `/chat_stream`
- `/chat_stream_cancel`
- `/chat_reset`
- `/health`
- `/knowledge/*`、`/evaluation/*`、`/runtime/*` 控制面领域 API
- API request / response schema
- SSE 文本序列化

---

## 2. Skill 适用范围

本 skill 适用于以下类型的工作：

1. 路由实现
2. API schema
3. SSE 序列化辅助
4. API 错误映射
5. cancel / reset / health 入口
6. API 层测试与 HTTP 集成测试

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
API 层负责收请求、校验、调 service、返回 JSON / SSE。
不负责业务状态机和内部编排。

### 4.2 SSE 是协议，不是业务状态机
`/chat_stream` 负责建立 `text/event-stream` 并序列化 canonical event。

### 4.3 外部契约必须稳定
当前 `/chat`、`/chat_stream`、`/chat_stream_cancel`、`/chat_reset`、`/health` 的契约必须保持稳定。

### 4.4 当前代码已落地 citations 输出
当前 `/chat` 与 `/chat_stream` completed 已有 citations 字段。
citation 业务语义不得在 API 层自行生成。
`/chat` 入口应直接调用当前正式 service 接口，不保留历史方法名兼容分支。

### 4.5 错误必须映射为清晰 HTTP 语义
API 层负责将 service / provider 层错误转换成可理解的 HTTP 错误响应。

### 4.6 控制面 API 必须按领域命名
控制面 API 文件、URL 分组与 schema 应按领域职责命名，而不是按当前消费者命名。
当前推荐收敛为：
- `chat.py`
- `knowledge.py`
- `evaluation.py`
- `runtime.py`

---

## 5. 默认阶段基线

当前 skill 默认基线如下：

- API 框架：FastAPI
- 流式协议：SSE
- `/chat_stream` 返回 `text/event-stream`
- `/chat_stream_cancel` 负责显式取消语义
- `/chat_reset` 负责上下文重置入口
- `/chat` 与 `/chat_stream` completed 包含 citations
- 控制面 API 采用 REST JSON，按 knowledge / evaluation / runtime 分组

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
5. cancel / reset / health 入口更新
6. API 层测试更新

仅给概念说明、不落代码、不补测试，不视为完成。

---

## 8. 实现约束

### 8.1 薄路由约束
API 层必须保持薄路由，不得把 business orchestration 写进 route handler。
不允许在 route 中保留“新旧 service 方法名双轨调用”的历史兼容逻辑。

### 8.2 SSE 约束
- SSE 文本格式化留在 API 层
- event name 必须稳定
- payload 必须来自 service 已归一化结果

### 8.3 cancel / reset 约束
- `/chat_stream_cancel` 只负责接入与转发取消请求
- `/chat_reset` 只负责接入与转发上下文重置请求

### 8.4 错误映射约束
- API 必须将底层异常映射为稳定 HTTP 语义
- 不直接暴露 provider / service traceback

### 8.5 Phase 6 约束
当前代码已输出 citations。
后续改动必须由真实代码与 schema 一起落地。

### 8.6 命名收敛约束
不允许继续新增 `*_console.py` 或等价消费者导向命名的正式 API 文件。

---

## 9. 与其他模块的协作约束

### 与 services 协作
services 负责编排；api 负责接入与返回。

### 与 schemas 协作
API 层的 request / response / event 必须通过 schema 表达。

### 与 context 协作
API 层不直接访问 context manager。
重置、状态变化都应经由 service 暴露。

### 与 rag 协作
API 层不直接访问 retrieval / index / embedding。
当前通过 service 结果输出 citations，但不直接组织 citation 业务逻辑。

---

## 10. 测试要求

API 相关实现至少补以下测试之一或多项：

1. `/chat` 正常响应测试
2. `/chat_stream` SSE 响应测试
3. `/chat_stream_cancel` 测试
4. `/chat_reset` 测试
5. `/health` 测试
6. error mapping 测试
7. HTTP 集成测试
8. `/chat` / `/chat_stream` citations 契约测试
9. knowledge / evaluation / runtime 控制面契约测试

---

## 11. Review 要点

提交前至少自查：

1. API 是否仍保持薄路由？
2. 是否没有把 retrieval / context / provider 逻辑混入 API 层？
3. 当前契约是否仍与 `app/api/schemas/chat.py` 一致？
4. citations 是否只作为 schema 契约字段透传？
5. 是否补了测试？

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

本 skill 的目标，是确保 `app/api/` 在当前项目中持续作为 HTTP / SSE 接入层演进，稳定承接 chat / stream / cancel / reset / health 协议与 citations 契约透传，而不把 retrieval 业务语义下沉到 API 层。
