# delivery-workflow.md

## 1. 目的

本文件定义 `python-observability-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- `log_report`
- JSON-safe 序列化
- 事实型日志字段
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
- 不把未落地 retrieval / citation 字段写成现有能力

### 步骤 4：实现
要求：
- JSON-safe
- 事实型日志
- 不侵入主链路职责
- 不泄漏敏感正文

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- 是否仍是基础设施层？
- 是否保证 JSON-safe？
- 是否没有把业务逻辑混进来？
- 是否没有凭空声明未落地字段？

---

## 3. 禁止跳步

禁止：

- 未读文档直接改代码
- 不补测试直接提交
- 用 observability 代码替代业务状态机
