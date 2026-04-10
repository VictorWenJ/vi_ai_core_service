# delivery-workflow.md

## 1. 目的

本文件定义 `python-observability-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- structured logging
- json-safe serialization
- request trace
- stream trace
- retrieval trace
- citation trace
- observability tests

### 步骤 2：阅读治理文档
至少阅读：

- 根目录四文档
- `app/observability/AGENTS.md`
- `skills/python-observability-capability/SKILL.md`

### 步骤 3：设计最小增量
要求：
- 不推倒重来
- 不越界改动
- 不改动无关模块风格

### 步骤 4：实现
要求：
- 事实型记录
- JSON-safe
- 不侵入业务逻辑
- 不泄漏敏感正文

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- 日志是否仍为结构化？
- 是否 JSON-safe？
- 是否没有把业务逻辑混进 observability？
- retrieval / citation 字段是否齐全？
- 是否仍符合模块边界？

---

## 3. 禁止跳步

禁止：

- 未读文档直接改代码
- 不补测试直接提交
- 未确认边界直接把 observability 改成“全能调度层”