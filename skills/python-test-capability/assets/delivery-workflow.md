# delivery-workflow.md

## 1. 目的

本文件定义 `python-test-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- API contract test
- sync / stream test
- lifecycle test
- request assembly test
- provider / prompt / config test

### 步骤 2：阅读治理文档
至少阅读：

- 根目录四文档
- `tests/AGENTS.md`
- `skills/python-test-capability/SKILL.md`

### 步骤 3：设计最小增量
要求：
- 不推倒重来
- 不把未落地能力写成已覆盖
- 优先保护已落地主链路

### 步骤 4：实现
要求：
- 用例稳定
- 边界明确
- completed / failed / cancelled 区分清晰

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- 是否保护了关键主链路？
- 是否覆盖了 assembly 顺序？
- 是否没有把未落地 retrieval / citation 写成现有覆盖？
- 是否仍符合模块边界？

---

## 3. 禁止跳步

禁止：

- 未读文档直接写测试
- 不理解目标行为就先堆 mock
- 用“已有测试”掩盖真实回归缺口
