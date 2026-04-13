# delivery-workflow.md

## 1. 目的

本文件定义 `python-service-capability` 在实际开发中的标准交付流程。

---

## 2. 标准流程

### 步骤 1：确认任务边界
先确认本轮需求属于以下哪类：

- sync chat façade
- stream chat façade
- request assembly 协作
- cancellation registry
- service errors
- service tests

### 步骤 2：阅读治理文档
至少阅读：

- 根目录四文档
- `app/services/AGENTS.md`
- `skills/python-service-capability/SKILL.md`

### 步骤 3：设计最小增量
要求：
- 不推倒重来
- 不越界改动
- 不把未落地能力写成已实现逻辑

### 步骤 4：实现
要求：
- services 仍保持 façade 层定位
- request_assembler 仍是唯一装配中枢
- 同步与流式都通过 chat runtime 执行
- 不混入 SDK、路由或 store 细节

### 步骤 5：补测试
至少补当前改动直接相关的测试。

### 步骤 6：自检
至少回答：
- services 是否仍然只是 façade？
- 是否没有把 workflow / hook / trace 塞回 services？
- SSE 交付路径是否仍稳定？
- request assembly 顺序是否仍正确？
- 是否仍符合模块边界？

---

## 3. 禁止跳步

禁止：

- 未读文档直接改代码
- 不补测试直接提交
- 在 services 层直接散落路由、SDK、存储或 runtime 主逻辑
