# SKILL.md

> skill_name: python-rag-capability  
> module_scope: app/rag/  
> status: active  
> last_updated: 2026-04-10

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `app/rag/` 子域中进行 RAG / Knowledge + Citation Layer 的设计、实现、测试与增量演进。

本 skill 的目标不是生成“泛化的 RAG 示例代码”，而是约束在本项目文档治理体系下，按企业级 AI 应用的标准实现内部知识增强能力。

---

## 2. Skill 适用范围

本 skill 适用于以下类型的工作：

1. 知识对象模型设计
2. ingest pipeline 设计与实现
3. parser / cleaner / chunker 开发
4. embedding provider 接入
5. vector index 抽象与实现
6. retrieval service 开发
7. citation 数据结构与格式化
8. 与 chat / stream 主链路的知识增强接入
9. retrieval 相关测试与可观测性补充

---

## 3. Skill 不适用范围

本 skill 不用于以下工作：

1. API 路由设计
2. 同步或流式 chat 主链路编排
3. conversation short-term memory 实现
4. provider chat completion 主链路实现
5. 审批流
6. Case Workspace
7. 长期记忆平台
8. Agent Runtime
9. 多模态主链路检索

如任务超出上述边界，应转交对应模块 skill 处理。

---

## 4. 本 skill 的核心原则

### 4.1 先做内部子域，不拆独立服务
当前阶段，RAG 必须作为 `vi_ai_core_service` 内部子域实现。  
不得在未获明确确认前擅自演进为独立微服务。

### 4.2 先做最小可用闭环，不做平台化膨胀
当前目标是建立：

- ingest
- chunk
- embedding
- index
- retrieval
- citation

的最小可用闭环。  
不提前建设大而全知识平台。

### 4.3 citation 是一等能力
所有知识增强链路必须以“可引用、可追溯”为目标。  
citation 不是后期附加字段，而是 Phase 6 的核心交付能力。

### 4.4 retrieval 不替代 short-term memory
RAG 负责外部知识 grounding。  
Phase 4 的 recent raw / rolling summary / working memory 仍然独立存在。

### 4.5 失败可降级
RAG 是增强层。  
retrieval / embedding / index 异常不应无条件拖垮 chat 主链路。

---

## 5. 默认技术基线

当前 skill 默认技术基线如下：

- 向量数据库：Qdrant
- 相似度度量：Cosine
- embedding：单一文本 embedding 基线
- chunking：结构感知 + token-aware + overlap
- retrieval：top-k + metadata filter
- citation：由 retrieval 结果派生，不由模型自由生成

如需变更该基线，必须在根文档与模块 AGENTS 中先更新，再执行实现。

---

## 6. 标准执行流程

执行 `app/rag/` 相关任务时，必须遵循以下顺序：

1. 阅读根目录文档  
   - `AGENTS.md`
   - `PROJECT_PLAN.md`
   - `ARCHITECTURE.md`
   - `CODE_REVIEW.md`

2. 阅读模块文档  
   - `app/rag/AGENTS.md`

3. 阅读本 skill  
   - `skills/python-rag-capability/SKILL.md`

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

RAG 相关实现任务，至少应交付以下之一或多项：

1. 新增/更新知识对象模型
2. 新增/更新 ingest pipeline
3. 新增/更新 retrieval service
4. 新增/更新 citation 结构
5. 新增/更新 request assembly 知识接入逻辑
6. 新增/更新测试
7. 新增/更新 observability 字段

仅给概念说明、不落代码、不补测试，不视为完成。

---

## 8. 实现约束

### 8.1 模型约束
必须显式区分：
- KnowledgeDocument
- KnowledgeChunk
- RetrievedChunk
- Citation

不得混用“一个 dict 到处传”。

### 8.2 chunking 约束
正式主策略必须为：
- 结构感知
- token-aware
- overlap

不得继续使用按字符硬切分作为正式策略。

### 8.3 index 约束
必须通过统一抽象暴露索引能力。  
不得将底层向量库 SDK 调用散落到多个业务文件。

### 8.4 retrieval 约束
retrieval service 必须独立，不得直接嵌入 chat service 的实现细节中。

### 8.5 citation 约束
citation 必须来源于 retrieval 结果。  
不得将 citation 设计为模型自由输出文本。

---

## 9. 与其他模块的协作约束

### 与 services 协作
`services` 负责编排；`rag` 负责提供 retrieval 与 citation-ready 数据。  
`rag` 不编排 chat 主链路。

### 与 context 协作
`context` 管 short-term memory；`rag` 管外部知识 grounding。  
两者不得互相替代。

### 与 providers 协作
embedding 可以通过 `providers` 暴露的 embedding 抽象实现。  
`rag` 不直接承担 chat provider 职责。

### 与 api / schemas 协作
citation 最终如何对外返回，由 `schemas` 与 `api/services` 共同完成。  
`rag` 只提供 citation-ready 结构。

---

## 10. 测试要求

RAG 相关实现至少补以下测试之一或多项：

1. parser 测试
2. chunker 测试
3. embedding provider 适配测试
4. index upsert / query 测试
5. retrieval service 测试
6. citation 格式化测试
7. `/chat` citation 输出测试
8. `/chat_stream` completed citation 输出测试
9. retrieval 失败降级测试

---

## 11. Review 要点

提交前至少自查：

1. 是否仍在 `app/rag/` 边界内？
2. 是否把 retrieval 与 short-term memory 混淆了？
3. 是否把 SDK 调用散落到了不该散落的地方？
4. 是否仍然保持 Qdrant + Cosine + 文本 embedding 基线？
5. 是否有 citation 输出能力？
6. 是否补了测试？
7. 是否破坏了同步或流式 chat 主链路？

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

本 skill 的目标，是确保 `app/rag/` 在当前项目中以企业级、可增量演进、可测试、可审查的方式落地 Phase 6：Knowledge + Citation Layer，而不是演化成一个脱离项目主线的泛化 RAG 示例模块。