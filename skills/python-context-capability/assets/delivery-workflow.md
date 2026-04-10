# delivery-workflow.md

## 1. 目的

本文件定义 `python-context-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- models
- manager
- stores
- codec / serialization
- lifecycle state
- layered memory
- request assembly 过滤支持
- context tests

### 步骤 2：阅读治理文档
至少阅读：

- 根目录四文档
- `app/context/AGENTS.md`
- `skills/python-context-capability/SKILL.md`

### 步骤 3：设计最小增量
要求：
- 不推倒重来
- 不越界改动
- 不改动无关模块风格

### 步骤 4：实现
要求：
- 模型清晰
- 边界清晰
- lifecycle 语义清晰
- 不把 retrieval 逻辑写进 context

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- `ContextWindow.messages` 语义是否正确？
- 是否只有 completed 才进入标准 memory update？
- 是否没有混入 retrieval / citation 语义？
- store codec 是否稳定？
- 是否仍符合模块边界？

---

## 3. 禁止跳步

禁止：

- 未读文档直接改代码
- 不补测试直接提交
- 未确认边界直接把 context 改成“全能状态中心”