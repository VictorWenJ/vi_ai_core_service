# delivery-workflow.md

## 1. 目的

本文件定义 `python-api-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- chat route
- stream route
- cancel route
- reset route
- health route
- schema
- sse formatting
- error mapping
- api tests

### 步骤 2：阅读治理文档
至少阅读：

- 根目录四文档
- `app/api/AGENTS.md`
- `skills/python-api-capability/SKILL.md`

### 步骤 3：设计最小增量
要求：
- 不推倒重来
- 不越界改动
- 不改动无关模块风格

### 步骤 4：实现
要求：
- route 保持薄
- schema 清晰
- 错误映射稳定
- SSE 输出稳定

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- API 是否仍只做协议职责？
- 是否没有混入 retrieval / context / provider 逻辑？
- SSE 是否稳定？
- citations 输出是否符合当前阶段边界？
- 是否仍符合模块边界？

---

## 3. 禁止跳步

禁止：

- 未读文档直接改代码
- 不补测试直接提交
- 未确认边界直接把 API 改成厚编排层