# app/services/AGENTS.md

## 1. 文档定位

本文件定义 `app/services/` 目录的职责、边界、结构约束、演进方向与代码审查标准。

当前阶段，本文件临时同时承担该模块的：

- AGENTS.md
- PROJECT_PLAN.md
- ARCHITECTURE.md
- CODE_REVIEW.md

功能。

本文件只约束应用编排层，不替代系统根目录文档。

---

## 2. 模块定位

`app/services/` 是系统的 **应用编排层**。

它负责串联 API 接入层与底层能力模块（context、prompts、providers），完成一次业务请求的主执行流程。

当前目录下已有文件：

- `llm_service.py`
- `prompt_service.py`
- `__init__.py`

---

## 3. 本层职责

应用编排层负责：

1. 承接 API 层传入的用例请求
2. 组织一次完整调用链路
3. 协调 `app/context/`、`app/prompts/`、`app/providers/`
4. 将底层能力拼装为可用业务流程
5. 做跨模块的流程控制、失败传播与结果封装
6. 保持系统主调用链路清晰稳定

一句话：**services 是“怎么把多个能力串起来”的地方。**

---

## 4. 本层不负责什么

应用编排层不负责：

1. 不负责 HTTP 路由定义
2. 不负责底层 provider HTTP/SDK 适配细节
3. 不负责 Prompt 模板文件资产管理细节
4. 不负责 context store 的底层存储实现
5. 不负责定义基础数据模型契约本身
6. 不负责把所有业务逻辑塞进一个超大 service

---

## 5. 依赖边界

### 允许依赖

`app/services/` 可以依赖：

- `app/context/`
- `app/prompts/`
- `app/providers/`
- `app/schemas/`
- 必要的配置模块

### 禁止依赖

`app/services/` 不应依赖：

- `app/api/`

说明：

- 调用方向应为 `api -> services -> lower layers`
- 绝不允许反向依赖 API 层，避免循环耦合

---

## 6. 当前结构理解

当前服务层建议理解为：

- `llm_service.py`
  - 主 LLM 请求编排入口
  - 负责把请求送入 provider 能力链路
- `prompt_service.py`
  - 对 prompt 获取、选择、渲染提供面向应用层的封装

如果未来能力增多，应按“用例/编排职责”继续拆分，例如：

- `chat_service.py`
- `completion_service.py`
- `provider_selection_service.py`
- `conversation_service.py`

不要把所有逻辑都留在 `llm_service.py` 里无限长大。

---

## 7. 架构原则

### 7.1 编排优先，细节下沉

services 负责“编排”，不负责“底层实现”。

例如：

- prompt 怎么渲染，细节在 `app/prompts/`
- provider 怎么适配，细节在 `app/providers/`
- context 怎么存，细节在 `app/context/`

### 7.2 单个 service 只承载一种主要编排职责

不要让某个 service 既做会话编排、又做 provider 选择、又做 prompt 版本治理、又做重试策略。

### 7.3 明确输入输出

service 的输入输出应尽量稳定、明确，便于：

- API 层调用
- 单元测试
- 错误定位
- 后续重构

### 7.4 保持主链路清晰

调用链要能让协作者快速回答：

- 请求从哪里进来
- 经过了哪些编排步骤
- 最终在哪里调用 provider
- 哪里处理上下文
- 哪里处理 prompt

---

## 8. 建议的调用思路

当前阶段，一个典型调用链应大致符合：

1. API 层接收请求
2. service 解析用例所需参数
3. service 获取上下文
4. service 调用 prompt 能力生成最终输入
5. service 调用 provider 能力完成模型请求
6. service 整理结果并返回 API 层

即使当前实现还比较轻，也应朝这个方向收敛。

---

## 9. 当前阶段演进计划

本层当前重点：

1. 保持 LLM 主调用链稳定
2. 控制 service 层复杂度
3. 明确 `llm_service` 与 `prompt_service` 的分工
4. 避免未来所有功能都堆进 `llm_service.py`

后续演进方向：

1. 将 service 层从“文件级”演进到“用例级”
2. 补充 provider 选择策略编排
3. 补充上下文装配策略编排
4. 为 streaming 能力预留编排入口
5. 为未来 agent/rag 接入保留服务层承接点

---

## 10. 修改规则

修改或新增 service 时，必须遵守：

1. service 要体现“用例编排”职责
2. 不要直接在 service 中写过多 provider 私有协议细节
3. 不要在 service 中硬编码 prompt 文本
4. 不要在 service 中直接嵌入存储层实现细节
5. service 间依赖要克制，避免网状耦合
6. 如果某个 service 超过单一职责，应拆分

---

## 11. Code Review 清单

评审 `app/services/` 时，重点检查：

### 职责边界

- 代码是否仍然是编排层，而不是底层适配层
- 是否把 provider/context/prompts 的内部细节上提到了 service
- 是否把 HTTP 处理逻辑拉进来了

### 结构质量

- service 是否过长
- 是否出现“万能 service”
- 是否出现高耦合、难拆分的流程

### 流程正确性

- 主链路是否清晰
- 错误传播是否可理解
- 是否有隐式状态或隐藏副作用

### 可测试性

- 是否可对 service 单独做测试
- 是否方便 mock provider / prompt / context
- 是否覆盖成功和失败场景

---

## 12. 测试要求

应用编排层建议至少覆盖：

1. 基本成功路径
2. prompt 获取/渲染失败路径
3. provider 调用失败路径
4. 参数异常传播路径
5. 上下文参与编排时的行为断言
6. 不同 provider 下的编排一致性

---

## 13. 禁止事项

以下做法应避免：

- 把 service 写成 API 层
- 把 service 写成 provider 适配层
- 把 service 写成 prompt 模板仓库
- 把所有业务都塞进一个文件
- 在 service 中出现大量硬编码厂商分支

---

## 14. 一句话总结

`app/services/` 是系统的业务主链路编排层，负责 **组织流程**，不负责替代底层能力模块本身。

---

## 15. 本模块任务执行链路（强制）

Services 类任务必须按以下顺序执行：

1. 先读根目录四文档
2. 再读本文件
3. 再按编排涉及能力匹配 skill：
   - API 编排相关：`skills/python-api-capability/`
   - Context 编排相关：`skills/python-context-capability/`
   - Prompt 编排相关：`skills/python-prompt-capability/`
   - Provider 编排相关：`skills/python-ai-provider-capability/` 或 `skills/python-llm-provider-capability/`
4. 再改 `app/services/` 代码
5. 再按根 `CODE_REVIEW.md` + 本文件 + 对应 skill checklist 自审
6. 若编排边界或主链路事实变化，回写文档

---

## 16. 本模块交付门禁（新增）

- 发现 service 越权承载 API/provider/prompt/context 细节时必须先整改
- 变更主链路时必须补充或更新 service 级测试
- 未完成文档回写一致性检查，不视为完成
