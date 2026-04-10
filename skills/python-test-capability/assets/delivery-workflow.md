# delivery-workflow.md

## 1. 目的

本文件定义 `python-test-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- unit test
- integration test
- api contract test
- lifecycle test
- assembly test
- retrieval / citation test
- provider / prompt / schema test

### 步骤 2：阅读治理文档
至少阅读：

- 根目录四文档
- `tests/AGENTS.md`
- `skills/python-test-capability/SKILL.md`

### 步骤 3：设计最小增量
要求：
- 不推倒重来
- 不越界改动
- 不改动无关模块风格

### 步骤 4：实现
要求：
- 覆盖关键路径
- 覆盖关键差异路径
- 优先确定性
- 不用测试掩盖架构问题

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- 是否保护了关键主链路？
- 是否区分了 completed / failed / cancelled？
- 是否覆盖了 retrieval / citation 边界？
- 是否过度依赖真实外部服务？
- 是否仍符合模块边界？

---

## 3. 禁止跳步

禁止：

- 未读文档直接改测试
- 不理解主链路就写脆弱测试
- 未确认边界直接把 tests 改成“混乱脚本目录”