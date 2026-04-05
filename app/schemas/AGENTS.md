# app/schemas/AGENTS.md

> 更新日期：2026-04-06


## 1. 文档定位

本文件定义 `app/schemas/` 目录的职责、边界、结构约束、演进方向与代码审查标准。

当前阶段，本文件临时同时承担该模块的：

- AGENTS.md
- PROJECT_PLAN.md
- ARCHITECTURE.md
- CODE_REVIEW.md

功能。

本文件只约束数据模型层。

---

## 2. 模块定位

`app/schemas/` 是系统的 **数据模型层**。

它负责定义系统内外部交互使用的数据契约，使不同模块之间能以统一、清晰、稳定的方式交换数据。

当前目录下已有文件：

- `llm_request.py`
- `llm_response.py`
- `__init__.py`

---

## 3. 本层职责

数据模型层负责：

1. 定义请求模型
2. 定义响应模型
3. 作为跨模块的数据契约载体
4. 提供字段层面的语义稳定性
5. 为未来内部 canonical contract 演进打基础

一句话：**schemas 层负责“系统里传的数据长什么样”。**

---

## 4. 本层不负责什么

本层不负责：

1. 不负责业务流程编排
2. 不负责 HTTP 路由
3. 不负责 provider API 适配
4. 不负责 Prompt 资产管理
5. 不负责上下文存储
6. 不负责在 schema 中写复杂业务行为

---

## 5. 依赖边界

### 基本规则

`app/schemas/` 应尽量是系统中最稳定、最底层的共享契约层之一。

### 禁止依赖

`app/schemas/` 不应依赖：

- `app/api/`
- `app/services/`
- `app/context/`
- `app/prompts/`
- `app/providers/`

说明：

- 其他模块可以依赖 schema
- schema 不应反向依赖其他业务模块
- 这是避免循环依赖与契约污染的关键规则

---

## 6. 当前结构理解

建议当前目录职责如下：

- `llm_request.py`
  - 描述系统内部接收或传递的 LLM 请求契约
- `llm_response.py`
  - 描述系统内部返回或传递的 LLM 响应契约

后续如果契约增长，可再按类型拆分，例如：

- `chat_request.py`
- `chat_response.py`
- `provider_contracts.py`
- `usage.py`
- `errors.py`

但当前阶段不宜过度拆分。

---

## 7. 设计原则

### 7.1 契约稳定优先

schema 一旦被多个层使用，就不应频繁随意改字段语义。

### 7.2 字段含义明确

每个字段要能回答：

- 它表示什么
- 谁负责填充
- 谁负责消费
- 是否必填
- 是否未来可扩展

### 7.3 避免把业务逻辑塞进模型

schema 主要是数据契约，不是业务服务对象。  
不要在这里承载复杂流程逻辑。

### 7.4 内外契约逐步区分

当前可以先用较简单的 schema 结构。  
未来如果系统变复杂，应逐步区分：

- 外部 API contract
- 内部 canonical contract
- provider-specific temporary mapping contract

---

## 8. 当前阶段演进计划

本层当前目标：

1. 保持 `llm_request` / `llm_response` 清晰稳定
2. 为 services 与 providers 提供统一数据契约
3. 控制 schema 层膨胀速度
4. 避免一开始就拆成大量零散 contract 文件

### 当前阶段能力声明（强约束）

- 本阶段已实现并验收：
  - `llm_request` / `llm_response` 基础契约
  - 单轮非流式主链路所需字段稳定性
- 本阶段仅预留，不要求落地：
  - tools/function calling contract 完整落地
  - structured output contract 完整落地
  - 多模态 contract 完整落地
  - 大规模内外 contract 分层重构

后续演进方向：

1. 内外部契约分层
2. usage / token / metadata 合同补充
3. 错误契约统一
4. 结构化输出相关 contract
5. 工具调用 contract
6. 多模态 contract

---

## 9. 修改规则

修改 `app/schemas/` 时必须遵守：

1. 修改字段前先评估影响范围
2. 优先做兼容式演进，避免随意破坏调用方
3. 新增字段应具备清晰语义
4. 删除字段应极度谨慎
5. 不要引入对上层模块的依赖
6. 不要为了临时厂商需求污染通用 schema

---

## 10. Code Review 清单

评审 `app/schemas/` 时，重点检查：

### 契约清晰度

- 模型命名是否准确
- 字段命名是否清晰
- 字段语义是否稳定
- 是否容易理解

### 边界纯度

- schema 是否仍然保持为数据契约层
- 是否引入了业务逻辑
- 是否引入了不应有的模块依赖

### 兼容性

- 改动是否影响现有调用方
- 是否破坏 provider 归一化结果
- 是否导致 API/service/provider 对接混乱

### 扩展性

- 是否为未来 contract 细分留出空间
- 是否避免模型过早臃肿
- 是否避免字段泛滥

---

## 11. 测试要求

schema 层建议至少覆盖：

1. 基础模型构造
2. 必填字段约束
3. 默认值行为
4. 序列化/反序列化正确性
5. 关键字段兼容性断言

---

## 12. 禁止事项

以下做法应避免：

- 在 schema 中写复杂业务逻辑
- 让 schema 依赖 service/provider/api
- 为某个单一厂商临时字段污染整个通用 contract
- 模型命名含糊不清
- 字段语义频繁变动

---

## 13. 一句话总结

`app/schemas/` 是系统的数据契约层，负责 **定义稳定、清晰、可共享的数据模型**，而不是承担流程或适配逻辑。

---

## 14. 本模块任务执行链路（强制）

Schemas 类任务必须按以下顺序执行：

1. 先读根目录四文档
2. 再读本文件
3. 再按契约关联能力匹配 skill：
   - API 契约：`skills/python-api-capability/`
   - Prompt/Context/Provider 契约：对应能力 skill
4. 再改 `app/schemas/` 代码
5. 再按根 `CODE_REVIEW.md` + 本文件 + 对应 skill checklist 自审
6. 若契约事实变化，回写文档并标注影响范围

---

## 15. 本模块交付门禁（新增）

- 发现 schema 承担流程逻辑或反向依赖业务层时必须先整改
- 变更共享契约字段时必须补充或更新测试
- 未完成兼容性评估与文档回写，不视为完成
