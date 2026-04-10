# delivery-workflow.md

## 1. 目的

本文件定义 `python-schemas-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- `llm_request.py`
- `llm_response.py`
- dataclass 校验
- 内部 canonical contract 测试

### 步骤 2：阅读治理文档
至少阅读：

- 根目录四文档
- `app/schemas/AGENTS.md`
- `skills/python-schemas-capability/SKILL.md`

### 步骤 3：设计最小增量
要求：
- 不推倒重来
- 不把 API 对外契约混进 `app/schemas/`
- 不把未落地 citation / retrieval 写进默认基线

### 步骤 4：实现
要求：
- 命名清晰
- 校验清晰
- 语义稳定
- provider-agnostic

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- `app/schemas/` 是否仍只承载内部 canonical contract？
- 是否没有混入 API / citation / retrieval 对象？
- 流式与非流式语义是否仍一致？
- 是否仍符合模块边界？

---

## 3. 禁止跳步

禁止：

- 未读文档直接改代码
- 不补测试直接提交
- 在 `app/schemas/` 中混入无边界的“全量业务对象体系”
