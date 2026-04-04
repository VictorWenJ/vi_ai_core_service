# app/providers/AGENTS.md

## 1. 文档定位

本文件定义 `app/providers/` 目录的职责、边界、结构约束、演进方向与代码审查标准。

当前阶段，本文件临时同时承担该模块的：

- AGENTS.md
- PROJECT_PLAN.md
- ARCHITECTURE.md
- CODE_REVIEW.md

功能。

本文件只约束模型 API 接入层。

---

## 2. 模块定位

`app/providers/` 是系统的 **模型 API 接入层**。

它负责对接不同模型厂商或兼容协议，实现统一的 provider 抽象，并向上层暴露一致的模型调用能力。

当前目录下已有文件：

- `base.py`
- `openai_compatible_base.py`
- `registry.py`
- `openai_provider.py`
- `gemini_provider.py`
- `deepseek_provider.py`
- `doubao_provider.py`
- `tongyi_provider.py`
- `__init__.py`

---

## 3. 本层职责

模型 API 接入层负责：

1. 定义 provider 统一抽象
2. 对接不同厂商模型接口
3. 处理不同厂商协议差异
4. 将内部请求映射到厂商请求
5. 将厂商响应归一化为系统内部结果
6. 为上层屏蔽厂商差异
7. 管理 provider 注册与查找

一句话：**providers 层负责“如何接不同模型厂商，并对上提供统一能力”。**

---

## 4. 本层不负责什么

本层不负责：

1. 不负责 HTTP API 暴露
2. 不负责业务流程编排
3. 不负责 Prompt 资产管理
4. 不负责上下文存储
5. 不负责在 provider 中决定整个应用流程
6. 不负责把所有上层策略都塞进 provider

---

## 5. 依赖边界

### 允许依赖

`app/providers/` 可以依赖：

- `app/schemas/`
- 配置模块
- 标准库
- 必要的 HTTP/SDK 客户端基础设施

### 禁止依赖

`app/providers/` 不应依赖：

- `app/api/`
- `app/services/`
- `app/prompts/`
- `app/context/`

说明：

- provider 层应保持为独立适配层
- 上层调用 provider，provider 不应反向理解上层业务流程

---

## 6. 当前结构理解

建议当前结构职责如下：

- `base.py`
  - 定义 provider 统一抽象与公共契约
- `openai_compatible_base.py`
  - 承载 OpenAI 兼容协议族的公共实现
- `registry.py`
  - 管理 provider 注册、发现与构建
- `*_provider.py`
  - 具体厂商实现

这种结构的核心目标是：

- 共性抽到 base
- 兼容族共性抽到 compatible base
- 厂商差异留在 concrete provider
- 上层通过统一接口使用

---

## 7. 架构原则

### 7.1 统一抽象优先

系统内部必须优先围绕统一 provider 抽象设计，而不是围绕单一厂商 SDK 设计。

### 7.2 协议差异向下吸收

厂商差异应尽量在 provider 层被吸收，不要外溢到 service 层或 API 层。

### 7.3 归一化结果稳定

provider 返回给上层的结果应尽量稳定，避免让上层处理一堆厂商特例。

### 7.4 共性上提，个性下沉

- 可复用的逻辑提到 `base.py` 或 `openai_compatible_base.py`
- 厂商私有差异留在具体 provider 文件中

### 7.5 新 provider 接入成本可控

新增 provider 应是“按规范接入新实现”，而不是“复制粘贴一份旧代码再魔改”。

---

## 8. 新增 Provider 的规则

新增 provider 时，必须遵守：

1. 先判断是否已有可复用的 base
2. 明确该 provider 属于：
   - 通用独立实现
   - OpenAI-compatible 家族
3. 必须接入统一 registry
4. 必须遵守系统内部请求/响应归一化契约
5. 不允许把厂商特殊字段无限上抛到 service 层
6. 必须补测试，至少覆盖：
   - 初始化/注册
   - 请求构造
   - 响应归一化
   - 错误处理

---

## 9. 当前阶段演进计划

本层当前目标：

1. 稳定统一 provider 抽象
2. 保持已接入厂商的一致性
3. 保持 OpenAI-compatible 基类可复用
4. 保持 registry 入口清晰

### 当前阶段能力声明（强约束）

- 本阶段已实现并验收：
  - 非流式文本 chat 主路径
  - provider 注册与发现
  - 基础 request/response 归一化
- 本阶段仅预留，不要求落地：
  - streaming 真实输出
  - 多模态真实输入映射
  - tools/function calling 真实能力
  - structured output 真实能力
  - 自动 fallback / retry / routing 引擎

后续演进方向：

1. streaming 能力
2. usage / token 统计归一化
3. 错误码归一化
4. timeout / retry / fallback 支持
5. capability matrix（文本、多模态、工具调用、结构化输出）
6. provider 级集成测试体系

---

## 10. 修改规则

修改 `app/providers/` 时，必须优先检查：

1. 是否破坏统一抽象
2. 是否把厂商私有逻辑泄漏到上层
3. 是否存在重复实现而未抽共性
4. 是否影响现有 registry 行为
5. 是否改变归一化结果结构
6. 是否引入隐藏兼容性问题

---

## 11. Code Review 清单

评审 `app/providers/` 时，重点检查：

### 抽象边界

- 是否仍然围绕统一 provider 抽象实现
- 是否把上层业务逻辑带入 provider
- 是否产生跨厂商耦合混乱

### 复用与结构

- 是否已有可复用 base 却没有复用
- 是否在具体 provider 中复制大量相同逻辑
- registry 是否仍然清晰

### 兼容性与归一化

- 请求是否正确映射到厂商格式
- 响应是否被正确归一化
- 错误是否可被上层稳定理解

### 可测试性

- 是否容易对单个 provider 做隔离测试
- 是否有标准化测试矩阵
- 是否覆盖失败与边界路径

---

## 12. 测试要求

provider 层建议至少覆盖：

1. provider 注册与发现
2. 配置读取与初始化
3. 请求结构映射
4. 响应结构归一化
5. 异常/错误映射
6. OpenAI-compatible 基类复用行为
7. 各 provider 的最小可用调用路径

---

## 13. 禁止事项

以下做法应避免：

- 在 provider 中写业务主流程
- 在 provider 中拼装 prompt 资产逻辑
- 在 provider 中持有上下文管理职责
- 在 service 层散落厂商特例补丁，反而不回收至 provider
- 新增 provider 只靠复制旧实现而不抽象共性

---

## 14. 一句话总结

`app/providers/` 是系统的模型接入适配层，负责 **统一抽象、协议适配、结果归一化与 provider 注册管理**。

---

## 15. 本模块任务执行链路（强制）

Provider 类任务必须按以下顺序执行：

1. 先读根目录四文档
2. 再读本文件
3. 再按任务类型选择 skill：
   - 通用 provider：`skills/python-ai-provider-capability/`
   - LLM provider：`skills/python-llm-provider-capability/`
4. 执行选中 skill 的 `SKILL.md` + checklist/test matrix/reference
5. 再改 `app/providers/` 代码
6. 再按根 `CODE_REVIEW.md` + 本文件 + skill checklist 自审
7. 若 provider contract/能力声明/边界事实变化，回写文档

---

## 16. 本模块交付门禁（新增）

- 发现 provider 逻辑外溢到 API/service 层时必须先整改
- 变更 request/response/stream 归一化行为时必须补充或更新测试
- 未通过对应 provider skill checklist，不视为完成
