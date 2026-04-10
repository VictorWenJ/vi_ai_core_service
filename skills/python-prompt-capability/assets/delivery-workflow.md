# delivery-workflow.md

## 1. 目的

本文件定义 `python-prompt-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- template file
- registry
- renderer
- variable rendering
- template organization
- prompt tests

### 步骤 2：阅读治理文档
至少阅读：

- 根目录四文档
- `app/prompts/AGENTS.md`
- `skills/python-prompt-capability/SKILL.md`

### 步骤 3：设计最小增量
要求：
- 不推倒重来
- 不越界改动
- 不改动无关模块风格

### 步骤 4：实现
要求：
- Prompt 资产化
- registry 显式
- renderer 单一职责
- 不混入业务逻辑

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- Prompt 是否真正沉淀为资产？
- registry 是否清晰？
- renderer 是否仍只负责渲染？
- 是否没有把业务逻辑混入 Prompt 层？
- 是否仍符合模块边界？

---

## 3. 禁止跳步

禁止：

- 未读文档直接改代码
- 不补测试直接提交
- 未确认边界直接把 prompts 改成“编排引擎”