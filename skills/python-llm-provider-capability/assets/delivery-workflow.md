# delivery-workflow.md

## 1. 目的

本文件定义 `python-llm-provider-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- provider 抽象
- implemented provider
- scaffolded provider
- registry / maturity
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
- 不把 embedding 写成当前已实现能力

### 步骤 4：实现
要求：
- canonical contract 清晰
- 错误映射清晰
- implemented / scaffolded 区分清晰
- 不混入业务编排逻辑

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- providers 是否仍是接入层？
- canonical contract 是否稳定？
- 成熟度声明是否与代码一致？
- 是否没有混入 retrieval / citation？

---

## 3. 禁止跳步

禁止：

- 未读文档直接改代码
- 不补测试直接提交
- 在 provider 层混入业务编排或未落地 embedding 规划
