# delivery-workflow.md

## 1. 目的

本文件定义 `python-schema-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- chat request / response
- stream event
- cancel
- reset
- lifecycle
- citation
- schema tests

### 步骤 2：阅读治理文档
至少阅读：

- 根目录四文档
- `app/schemas/AGENTS.md`
- `skills/python-schema-capability/SKILL.md`

### 步骤 3：设计最小增量
要求：
- 不推倒重来
- 不越界改动
- 不改动无关模块风格

### 步骤 4：实现
要求：
- contract 清晰
- 命名稳定
- 不泄漏内部对象
- 不破坏兼容性

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- schema 是否仍然是共享契约？
- 是否没有透传内部对象？
- `/chat` 与 `/chat_stream` 语义是否一致？
- citations 是否进入正式 contract？
- 是否仍符合模块边界？

---

## 3. 禁止跳步

禁止：

- 未读文档直接改代码
- 不补测试直接提交
- 未确认边界直接把 schemas 改成“全量业务对象层”