# delivery-workflow.md

## 1. 目的

本文件定义 `python-rag-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- 首次落地 `app/rag/` 运行时代码
- 知识对象模型
- ingest pipeline
- retrieval service
- citation 结构
- RAG tests

### 步骤 2：阅读治理文档
至少阅读：

- 根目录四文档
- `app/rag/AGENTS.md`
- `skills/python-rag-capability/SKILL.md`

### 步骤 3：设计最小增量
要求：
- 不推倒重来
- 不脱离当前仓库主线
- 不把空目录继续写成已实现模块

### 步骤 4：实现
要求：
- 目录落位清晰
- ingestion / retrieval 分离
- 与 services / context / providers 边界清晰
- citations 来自 retrieval

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- 当前提交是否真的新增了运行时代码？
- 是否仍保持内部子域定位？
- 是否没有把 retrieval 当作 short-term memory？
- 是否没有把未落地能力继续写进文档完成态？

---

## 3. 禁止跳步

禁止：

- 未读文档直接开做 RAG
- 不补测试直接提交
- 在没有实际代码的前提下继续扩大 Phase 6 完成态描述
