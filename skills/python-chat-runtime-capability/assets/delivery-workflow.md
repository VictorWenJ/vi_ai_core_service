# delivery-workflow.md

## 1. 目的

本文件定义 `python-chat-runtime-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- workflow 定义
- hook 定义
- engine 执行逻辑
- trace 收口
- runtime 模型
- runtime 测试

### 步骤 2：阅读治理文档
至少阅读：

- 根目录四文档
- `app/chat_runtime/AGENTS.md`
- `skills/python-chat-runtime-capability/SKILL.md`

### 步骤 3：设计最小增量
要求：
- 不推倒重来
- 不越界改动
- 不把未落地能力写成已实现逻辑

### 步骤 4：实现
要求：
- workflow 显式
- hook 独立配置
- sync / stream 共语义
- trace 统一收口
- 不混入 Tool / Agent / runtime skill loader

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- workflow 是否足够直观？
- hook 与 workflow 是否边界清晰？
- sync / stream 是否仍共享同一套主语义？
- 是否仍符合模块边界？

---

## 3. 禁止跳步

禁止：

- 未读文档直接改代码
- 不补测试直接提交
- 在 runtime 中一口气引入 Tool / Agent / runtime skill loader
