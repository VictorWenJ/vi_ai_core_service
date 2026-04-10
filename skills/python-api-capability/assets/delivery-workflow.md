# delivery-workflow.md

## 1. 目的

本文件定义 `python-api-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- route
- API schema
- SSE serialization
- error mapping
- cancel / reset / health
- API tests

### 步骤 2：阅读治理文档
至少阅读：

- 根目录四文档
- `app/api/AGENTS.md`
- `skills/python-api-capability/SKILL.md`

### 步骤 3：设计最小增量
要求：
- 不推倒重来
- 不越界改动
- 不把未落地字段写成已实现字段

### 步骤 4：实现
要求：
- route 薄
- schema 清晰
- SSE 稳定
- 错误映射可理解

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- API 是否仍保持薄路由？
- 是否仍与 `app/api/schemas/chat.py` 一致？
- 是否没有混入 retrieval / context / provider 逻辑？
- citations 是否只做契约透传？

---

## 3. 禁止跳步

禁止：

- 未读文档直接改代码
- 不补测试直接提交
- 在 API 层堆业务编排逻辑
