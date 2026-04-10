# delivery-workflow.md

## 1. 目的

本文件定义 `python-prompt-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- 模板文件
- registry
- renderer
- Prompt variables
- Prompt tests

### 步骤 2：阅读治理文档
至少阅读：

- 根目录四文档
- `app/prompts/AGENTS.md`
- `skills/python-prompt-capability/SKILL.md`

### 步骤 3：设计最小增量
要求：
- 不推倒重来
- 不越界改动
- 不把未落地的平台化能力写成已实现事实

### 步骤 4：实现
要求：
- 资产清晰
- registry 与 renderer 分离
- 模板可读
- 不把业务控制流写进模板

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- Prompt 是否真正沉淀为资产？
- registry / renderer 是否仍职责清晰？
- 是否没有把未落地能力写成已实现？
- 是否仍符合模块边界？

---

## 3. 禁止跳步

禁止：

- 未读文档直接改代码
- 不补测试直接提交
- 在 services / providers 中长期散落 prompt 字符串
