# delivery-workflow.md

## 1. 目的

本文件定义 `python-rag-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- ingestion
- chunking
- embedding
- indexing
- retrieval
- citation
- request assembly 接入
- 测试补充

### 步骤 2：阅读治理文档
至少阅读：

- 根目录四文档
- `app/rag/AGENTS.md`
- `skills/python-rag-capability/SKILL.md`

### 步骤 3：设计最小增量
要求：
- 不推倒重来
- 不越界改动
- 不改动无关模块风格

### 步骤 4：实现
要求：
- 模型清晰
- 边界清晰
- 先抽象后接实现
- 不让底层 SDK 调用扩散

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- retrieval 是否可工作？
- citations 是否可输出？
- chat 主链路是否未被破坏？
- 是否有降级路径？
- 是否仍符合模块边界？

---

## 3. 禁止跳步

禁止：

- 未读文档直接改代码
- 不补测试直接提交
- 未确认边界直接扩展为新平台