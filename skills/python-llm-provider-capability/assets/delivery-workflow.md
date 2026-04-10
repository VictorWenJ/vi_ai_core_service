# delivery-workflow.md

## 1. 目的

本文件定义 `python-llm-provider-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- chat provider
- stream provider
- embedding provider
- canonical contract
- config / registry
- error mapping
- provider tests

### 步骤 2：阅读治理文档
至少阅读：

- 根目录四文档
- `app/providers/AGENTS.md`
- `skills/python-llm-provider-capability/SKILL.md`

### 步骤 3：设计最小增量
要求：
- 不推倒重来
- 不越界改动
- 不改动无关模块风格

### 步骤 4：实现
要求：
- provider 抽象清晰
- canonical contract 清晰
- 不把业务逻辑写进 provider
- 不把 retrieval 逻辑写进 provider

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- provider 是否仍为能力接入层？
- canonical contract 是否稳定？
- 是否没有混入 retrieval / context / citation？
- embedding 是否纳入统一治理？
- 是否仍符合模块边界？

---

## 3. 禁止跳步

禁止：

- 未读文档直接改代码
- 不补测试直接提交
- 未确认边界直接把 provider 改成“业务编排层”