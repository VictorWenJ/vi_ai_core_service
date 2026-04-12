# SKILL.md

> skill_name: python-rag-capability
> module_scope: app/rag/
> status: active
> last_updated: 2026-04-13

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `app/rag/` 子域中进行 Phase 6 已落地主链路之上的 Phase 7：RAG Evaluation + Offline Build Foundation 演进约束整理。

当前代码事实是：`app/rag/` 已有 Python 运行时代码并完成最小闭环。
因此，本 skill 的首要目标是约束后续迭代如何在当前仓库内持续演进离线构建与评估基础，而不是越界扩张。

---

## 2. Skill 适用范围

本 skill 适用于以下类型的工作：

1. `app/rag/` 运行时代码的持续迭代
2. 知识对象模型设计
3. ingest pipeline 设计与实现
4. retrieval service 设计与实现
5. citation 结构设计与实现
6. RAG 相关测试与 observability 补充
7. 离线构建元数据与构建质量门禁补充
8. 为 benchmark 提供稳定知识对象与标签支撑

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

### 4.1 代码事实优先
代码事实优先：已落地能力写清楚，未落地能力不得写成完成态。

### 4.2 先做内部子域，不拆独立服务
RAG 必须持续作为 `vi_ai_core_service` 内部子域落地。

### 4.3 retrieval 不替代 short-term memory
RAG 负责 external knowledge grounding；
Phase 4 的 recent raw / rolling summary / working memory 继续独立存在。

### 4.4 citation 是已落地的一等能力
citation 必须来自 retrieval 结果，不得由模型自由生成。

### 4.5 失败可降级
RAG 是增强层。
retrieval / embedding / index 异常不应无条件拖垮 chat 主链路。

### 4.6 Post-Phase 7 先做控制面持久化
### 4.7 文档加载器适配层可以引入成熟框架
Phase 7 优先做 benchmark、黄金集、build 元数据与质量门禁；
不把本轮扩张成独立知识平台、复杂 hybrid retrieval 平台或 agentic retrieval 系统。

### 4.7 文档加载器适配层可以引入成熟框架
文档加载器不是当前项目的核心差异化能力。
允许在 loader adapter 层引入 LangChain 等成熟框架，但不得让其接管内部知识模型、chunking、build、retrieval 与 citation 主链路。

---

## 5. 默认技术基线

当前 skill 默认技术基线如下：

- 向量数据库：Qdrant
- 相似度度量：Cosine
- embedding：单一文本 embedding 基线
- chunking：结构感知 + token-aware + overlap
- retrieval：top-k + metadata filter
- citation：由 retrieval 结果派生
- 评估：query / retrieval / citation / answer 分层标签
- 离线构建：build / version / strategy 元数据可追踪
- 文档加载：允许在 adapter 层接入 LangChain loaders 等成熟能力
- 当前代码已提供 `app/rag/evaluation/` 数据集模型、runner 与结果落盘
- 当前代码已提供离线构建 `build_documents`、manifest 增量约束与质量门禁

以上基线当前已在代码中落地并通过测试覆盖。

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

1. `app/rag/` 运行时代码
2. 知识对象模型
3. ingest pipeline
4. retrieval service
5. citation 结构
6. RAG 相关测试
7. RAG 相关 observability 字段
8. benchmark / build metadata 支撑

仅给概念说明、不落代码、不补测试，不视为完成。

---

## 8. 实现约束

### 8.1 运行时代码约束
新增能力时，必须先确认当前提交不只是文档补丁，而是真的在 `app/rag/` 新增或完善运行时代码。
不得继续把控制面聚合逻辑长期堆在 `console_service.py` 一类消费者导向文件中。

### 8.2 模型约束
必须显式区分：

- KnowledgeDocument
- KnowledgeChunk
- RetrievedChunk
- Citation

### 8.3 chunking 约束
正式主策略必须为：

- 结构感知
- token-aware
- overlap

### 8.4 index / retrieval 约束
向量索引与 retrieval service 必须保持清晰边界，不得把 SDK 调用散落到多个业务文件。

### 8.5 编排约束
RAG 负责知识实现；chat 主链路编排仍由 services 负责。

### 8.6 Post-Phase 7 控制面对象约束
若本轮新增构建能力，必须保证 `build_id`、`version_id`、`chunk_strategy_version`、`embedding_model_version` 等字段具备明确语义与可追踪性。

### 8.7 评估支撑约束
RAG 模块可为 benchmark 提供可引用的数据对象与检索结果支撑，但不在本模块内实现完整 benchmark runner。


### 8.8 中文字段注释与默认配置说明约束

1. 本模块中所有 `@dataclass` 定义的结构化对象，必须为每一个字段补充中文注释，说明字段含义。
2. 本模块中所有默认配置常量、默认阈值或默认限制项，必须补充中文注释；涉及 token、chars、seconds、ttl、size、top-k、threshold 等值时，必须明确单位或语义。
3. 上述中文注释属于交付物的一部分。除非字段或常量被明确删除，否则后续改动不得删除、不得改为英文、不得在重构中丢失。
4. 字段或配置项语义变化时，必须同步更新对应中文注释。

---

## 9. 与其他模块的协作约束

### 与 services 协作
services 负责编排；rag 负责 retrieval 与 citation-ready 数据。

### 与 context 协作
context 管 short-term memory；rag 管 external knowledge grounding。

### 与 providers 协作
如后续需要 embedding，可通过 providers 能力接入；
rag 不负责 chat provider 主链路。
rag 依赖路径应指向 `app/providers/embeddings/` 抽象与工厂入口，不在 `app/rag/` 内维护 embedding 厂商实现。

### 与 api / schemas 协作
citation 最终如何对外返回，由 `api/services` 与对外 schema 共同完成；
rag 只提供内部知识数据。

---

## 10. 测试要求

当前代码基线下，本模块已有运行时代码。
后续改动至少补以下测试之一或多项：

1. parser 测试
2. chunker 测试
3. embedding 适配测试
4. index upsert / query 测试
5. retrieval service 测试
6. citation 格式化测试
7. retrieval 失败降级测试
8. 构建元数据或质量门禁测试（若本轮新增）

---

## 11. Review 要点

提交前至少自查：

1. 当前提交是否真的在 `app/rag/` 落地了运行时代码改动？
2. 是否仍保持为内部子域，而不是偷渡成新平台？
3. 是否没有把 retrieval 与 short-term memory 混淆？
4. 是否没有把 SDK 调用散落到不该散落的地方？
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

本 skill 的目标，是确保 `app/rag/` 在当前项目中以真实代码和测试为基础持续演进 Phase 6，而不是让文档描述脱离代码事实。
