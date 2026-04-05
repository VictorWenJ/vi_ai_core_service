# app/prompts/AGENTS.md

> 更新日期：2026-04-06


## 1. 文档定位

本文件定义 `app/prompts/` 目录的职责、边界、结构约束、演进方向与代码审查标准。

当前阶段，本文件临时同时承担该模块的：

- AGENTS.md
- PROJECT_PLAN.md
- ARCHITECTURE.md
- CODE_REVIEW.md

功能。

本文件只约束 Prompt 资产层。

---

## 2. 模块定位

`app/prompts/` 是系统的 **Prompt 资产层**。

它负责管理、组织、注册和渲染 Prompt 模板资产，为应用编排层提供可复用、可维护的提示词能力。

当前目录下已有文件：

- `registry.py`
- `renderer.py`
- `templates/chat/default_system.md`
- `__init__.py`

---

## 3. 本层职责

Prompt 资产层负责：

1. 管理 Prompt 模板文件
2. 提供模板注册与查找能力
3. 提供模板渲染能力
4. 维护 Prompt 资产的命名、组织与引用规则
5. 为上层提供稳定的 Prompt 使用入口
6. 为未来版本化、场景化、组合化 Prompt 打基础

一句话：**prompts 层负责“Prompt 资产怎么存、怎么找、怎么渲染”。**

---

## 4. 本层不负责什么

本层不负责：

1. 不负责 HTTP 接口
2. 不负责业务流程编排
3. 不负责 provider API 适配
4. 不负责上下文存储
5. 不负责在模板文件中隐藏复杂业务判断
6. 不负责把整个应用逻辑写进 Prompt 模板

---

## 5. 依赖边界

### 允许依赖

`app/prompts/` 可以依赖：

- 标准库
- 模板渲染相关基础能力
- 自身模块

### 不建议依赖

`app/prompts/` 不应常规依赖：

- `app/api/`
- `app/services/`
- `app/providers/`
- `app/context/`

说明：

- Prompt 资产层应尽量保持独立、纯粹、可复用
- 上层可以调用 Prompt 层，但 Prompt 层不应感知业务流程细节

---

## 6. 当前结构理解

建议当前目录职责如下：

- `registry.py`
  - 管理模板名称与模板资源映射
- `renderer.py`
  - 根据模板与变量完成渲染
- `templates/`
  - 存放静态模板资产
- `templates/chat/default_system.md`
  - 当前 chat 场景下的默认系统提示词模板

未来如需扩展，应优先继续按“场景目录”组织，例如：

- `templates/chat/`
- `templates/summary/`
- `templates/rag/`
- `templates/tool_use/`

---

## 7. 设计原则

### 7.1 Prompt 是资产，不是随手字符串

Prompt 不应散落在 service 或 provider 代码中。  
需要复用、维护、审查的 Prompt，应尽量沉淀为模板资产。

### 7.2 注册与渲染分离

- registry 负责“找到哪个模板”
- renderer 负责“把模板变成最终文本”

不要把模板查找和模板渲染杂糅成一个难维护的实现。

### 7.3 模板文件保持可读性

模板要能让协作者直接读懂用途。  
不要写成极难维护的大段混合文本。

### 7.4 尽量避免在模板中藏复杂逻辑

复杂业务判断应放在应用编排层或上游准备阶段。  
模板层以资产表达为主，而不是承担应用控制流。

---

## 8. 当前阶段演进计划

本层当前目标：

1. 建立基础 Prompt 资产目录
2. 建立 registry + renderer 的最小闭环
3. 避免 Prompt 分散在各层硬编码
4. 让 chat 场景具有稳定默认模板入口

### 当前阶段能力声明（强约束）

- 本阶段已实现并验收：
  - 基础模板资产目录
  - registry + renderer 最小闭环
  - 单轮 chat 默认 system prompt 支撑
- 本阶段仅预留，不要求落地：
  - Prompt orchestration engine
  - 大规模 Prompt 版本治理平台
  - tools/structured output/multimodal 的完整提示编排体系

后续演进方向：

1. 多场景模板
2. 模板版本管理
3. Few-shot 示例资产化
4. Prompt 组合能力
5. Prompt 渲染前变量校验
6. Prompt 变更审查机制

---

## 9. 修改规则

修改 `app/prompts/` 时必须遵守：

1. 新增 Prompt 优先放在模板目录中，而不是 service 中硬编码
2. 模板命名必须体现业务场景，而不是体现临时实现
3. 模板变量必须清晰、稳定、可理解
4. registry 中的公开名称应尽量稳定
5. renderer 不要耦合具体业务流程
6. 模板中不要嵌入与 provider 强绑定的传输协议细节

---

## 10. 模板组织建议

模板组织建议遵循：

1. 按场景分目录
2. 按角色/用途命名
3. 模板文件名应可读、可推断
4. 不用 `temp.md`、`new.md`、`test2.md` 这类临时命名
5. 模板变更应考虑兼容现有调用方

---

## 11. Code Review 清单

评审 `app/prompts/` 时，重点检查：

### 资产边界

- Prompt 是否真正沉淀为资产
- 是否还有大量 prompt 硬编码散落在其他层
- 是否把业务流程逻辑误塞进模板或 renderer

### 命名与可维护性

- 模板命名是否清晰
- registry 名称是否稳定
- renderer 行为是否可理解

### 渲染安全与正确性

- 变量替换是否明确
- 是否容易产生缺参或错参
- 是否存在难以发现的渲染错误

### 可扩展性

- 是否便于新增模板
- 是否便于多场景扩展
- 是否避免后期 registry 混乱

---

## 12. 测试要求

Prompt 层建议至少覆盖：

1. 模板查找成功路径
2. 模板渲染成功路径
3. 缺失模板路径
4. 缺失变量路径
5. 默认 chat 模板可用性
6. 渲染结果基本断言

---

## 13. 禁止事项

以下做法应避免：

- 在 service 中长期硬编码大量 prompt
- 在 template 中写复杂控制流
- 在 renderer 中写业务分支
- registry 命名混乱且不可追踪
- 模板内容与场景目录不匹配

---

## 14. 一句话总结

`app/prompts/` 是系统的 Prompt 资产中心，负责 **模板资产管理、注册与渲染**，而不是承担应用主流程逻辑。

---

## 15. 本模块任务执行链路（强制）

Prompt 类任务必须按以下顺序执行：

1. 先读根目录四文档
2. 再读本文件
3. 再执行 `skills/python-prompt-capability/SKILL.md` 与其 checklist/reference
4. 再改 `app/prompts/` 代码/模板
5. 再按根 `CODE_REVIEW.md` + 本文件 + skill checklist 自审
6. 若 Prompt 资产结构或契约事实变化，回写文档

---

## 16. 本模块交付门禁（新增）

- 发现 Prompt 文本在无关层大面积散落时必须先收敛
- 变更模板注册与渲染行为时必须补充或更新测试
- 未通过 `python-prompt-capability` checklist，不视为完成
