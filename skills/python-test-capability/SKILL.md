# SKILL.md

> skill_name: python-test-capability  
> module_scope: tests/  
> status: active  
> last_updated: 2026-04-10

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `tests/` 模块中进行测试设计、实现、维护与回归保护建设。

本 skill 的目标不是生成“泛化的 pytest 示例”，而是约束在本项目文档治理体系下，按企业级 AI 应用的标准实现：

- 主链路回归保护
- 同步 / 流式差异路径验证
- context lifecycle 验证
- retrieval / citation 验证
- provider / schema / prompt 等基础模块验证
- 降级与异常路径验证

---

## 2. Skill 适用范围

本 skill 适用于以下类型的工作：

1. unit tests
2. integration tests
3. API contract tests
4. lifecycle tests
5. request assembly tests
6. retrieval / citation tests
7. provider canonical contract tests
8. prompt asset tests
9. fake / mock / in-memory test support

---

## 3. Skill 不适用范围

本 skill 不用于以下工作：

1. 业务实现本身
2. HTTP 路由实现
3. provider SDK 接入
4. retrieval / chunking / embedding / index 实现
5. 用测试替代架构设计
6. 用测试替代文档治理
7. 性能压测平台
8. 混沌工程平台

如任务超出上述边界，应转交对应模块 skill 处理。

---

## 4. 本 skill 的核心原则

### 4.1 测试服务于架构与回归保护
测试要证明：
- 主链路可用
- 边界未破坏
- 契约未漂移
- 阶段目标未回退

### 4.2 主回归优先确定性
优先使用：
- fake
- mock
- in-memory
- local deterministic fixtures

不要把主回归建立在不稳定的外部环境上。

### 4.3 Phase 6 重点验证 retrieval / citation
必须验证：
- `/chat` citations
- `/chat_stream` completed citations
- delta 无 citations
- retrieval 失败降级
- knowledge block 装配顺序

### 4.4 completed / failed / cancelled 必须严格区分
测试必须验证这三类路径的差异，而不是只看“最后是否有输出”。

### 4.5 测试不是遮羞布
如果实现边界错了，应该修实现，而不是只补测试。

---

## 5. 默认阶段基线

当前 skill 默认基线如下：

- 同步与流式主链路测试并存
- context lifecycle 测试并存
- request assembly 顺序测试
- retrieval / citation 测试在 Phase 6 纳入主回归
- 主回归优先 fake / in-memory
- 外部依赖集成测试仅作为补充

如需变更该基线，必须先更新根目录文档与模块 AGENTS，再进入实现。

---

## 6. 标准执行流程

执行 `tests/` 相关任务时，必须遵循以下顺序：

1. 阅读根目录文档  
   - `AGENTS.md`
   - `PROJECT_PLAN.md`
   - `ARCHITECTURE.md`
   - `CODE_REVIEW.md`

2. 阅读模块文档  
   - `tests/AGENTS.md`

3. 阅读本 skill  
   - `skills/python-test-capability/SKILL.md`

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

test 相关任务，至少应交付以下之一或多项：

1. unit test 更新
2. integration test 更新
3. API contract test 更新
4. retrieval / citation test 更新
5. lifecycle / assembly test 更新
6. fake / mock / in-memory 测试辅助更新

仅给概念说明、不落代码、不补测试，不视为完成。

---

## 8. 实现约束

### 8.1 主链路约束
必须覆盖：
- `/chat`
- `/chat_stream`
- cancel / reset
- completed / failed / cancelled

### 8.2 assembly 约束
必须对 request assembly 顺序提供测试保护。

### 8.3 retrieval 约束
Phase 6 后，至少验证：
- 有 retrieval 命中
- 无 retrieval 命中
- retrieval 失败降级
- citations 输出边界

### 8.4 provider / prompt / schema 约束
基础能力模块也必须有最小稳定测试，不应只测试 service happy path。

### 8.5 外部依赖约束
主回归不应强依赖：
- 真实 provider
- 真实 Qdrant
- 真实 Redis
除非是专门的集成测试补充。

---

## 9. 与其他模块的协作约束

### 与 api 协作
tests 负责验证 API contract，不负责实现 route。

### 与 services 协作
tests 负责验证编排语义，不负责实现 service。

### 与 context 协作
tests 负责验证 lifecycle 与 memory 收口，不负责实现 state 管理。

### 与 rag 协作
tests 负责验证 retrieval / citation 行为，不负责实现检索逻辑。

### 与 providers / prompts / schemas 协作
tests 负责验证这些基础模块的稳定性与回归面，不负责实现它们本身。

---

## 10. 测试要求

test 相关实现至少补以下测试之一或多项：

1. chat / stream 主链路测试
2. cancel / reset 测试
3. lifecycle 差异测试
4. request assembly 顺序测试
5. retrieval / citation 测试
6. provider canonical contract 测试
7. prompt registry / renderer 测试
8. schema contract 测试

---

## 11. Review 要点

提交前至少自查：

1. 是否覆盖了关键主链路？
2. 是否区分了 completed / failed / cancelled？
3. 是否覆盖了 Phase 6 retrieval / citation 边界？
4. 是否没有过度依赖真实外部服务？
5. 是否补了必要测试？
6. 是否没有把测试写成脆弱、难维护的实现细节镜像？

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

本 skill 的目标，是确保 `tests/` 在当前项目中以企业级、可增量演进、可测试、可审查的方式承担项目级回归保护职责，特别是在 Phase 6 中把 retrieval、citation、lifecycle 与同步/流式主链路纳入稳定测试面，而不是只停留在零散的 happy path 测试。