# app/prompts/AGENTS.md

> 更新日期：2026-04-10

## 1. 文档定位

本文件定义 `app/prompts/` 的职责、边界、结构约束、开发约束与 review 标准。
当前阶段，本文件临时同时承担该模块的 `AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW` 职责。
执行 prompts 相关任务时，必须先读根目录 `AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md`，再读本文件，再根据 skill `skills/python-prompt-capability/` 执行。

本文件不负责：

- 仓库级协作规则
- 你和我之间的交互流程
- 根目录阶段路线图
- 根目录级总体架构说明
- 根目录级 Code Review 总标准

这些内容分别由：

- 根目录 `AGENTS.md`
- 根目录 `PROJECT_PLAN.md`
- 根目录 `ARCHITECTURE.md`
- 根目录 `CODE_REVIEW.md`
- `CHAT_HANDOFF.md`

承担。

---

## 2. 模块定位

`app/prompts/` 是系统的 Prompt 资产层。
它负责管理、组织、注册和渲染 Prompt 模板资产，为应用编排层提供可复用、可维护的提示词能力。

当前目录下已有文件：

- `registry.py`
- `renderer.py`
- `templates/chat/default_system.md`
- `__init__.py`

---

## 3. 本模块职责

1. 管理 Prompt 模板文件
2. 提供模板注册与查找能力
3. 提供模板渲染能力
4. 维护 Prompt 资产的命名、组织与引用规则
5. 为上层提供稳定的 Prompt 使用入口
6. 在当前代码基线中维护 `chat.default_system` 这一个已注册模板

一句话：**prompts 层负责“Prompt 资产怎么存、怎么找、怎么渲染”。**

---

## 4. 本模块不负责什么

1. 不负责 HTTP 接口
2. 不负责业务流程编排
3. 不负责 provider API 适配
4. 不负责上下文存储
5. 不负责在模板文件中隐藏复杂业务判断
6. 不负责把整个应用逻辑写进 Prompt 模板

---

## 5. 依赖边界

### 允许依赖
- 标准库
- 模板渲染相关基础能力
- 自身模块

### 不建议依赖
- `app/api/`
- `app/services/`
- `app/providers/`
- `app/context/`
- `app/rag/`

说明：

- Prompt 资产层应尽量保持独立、纯粹、可复用
- 上层可以调用 Prompt 层，但 Prompt 层不应感知业务流程细节

---

## 6. 架构原则

### 6.1 Prompt 是资产，不是随手字符串
Prompt 不应散落在 service 或 provider 代码中。
需要复用、维护、审查的 Prompt，应尽量沉淀为模板资产。

### 6.2 注册与渲染分离
- `registry.py` 负责“找到哪个模板”
- `renderer.py` 负责“把模板变成最终文本”

不要把模板查找和模板渲染杂糅成一个难维护的实现。

### 6.3 模板文件保持可读性
模板要能让协作者直接读懂用途。
不要写成极难维护的大段混合文本。

### 6.4 尽量避免在模板中藏复杂逻辑
复杂业务判断应放在应用编排层或上游准备阶段。
模板层以资产表达为主，而不是承担应用控制流。

### 6.5 provider-agnostic
Prompt 层必须保持 provider-agnostic。
不得在模板、registry、renderer 中绑定厂商私有协议细节。

---

## 7. 当前阶段能力声明

当前本轮必须保持稳定：

- 基础 Prompt 资产目录
- registry + renderer 最小闭环
- chat 默认 system prompt 资产
- Prompt 资产与业务编排的边界清晰
- `PROMPT_TEMPLATE_MAP` 的显式映射
- 基于字符串替换的基础 renderer 行为

当前本轮必须兼容：

- Phase 4 / Phase 5 的 chat 主链路
- 后续 Phase 6 知识增强接入时 Prompt 资产继续稳定使用

当前本轮不要求完整落地：

- Prompt 编排引擎
- Prompt 版本治理平台
- tools / 结构化输出 / multimodal 的完整提示编排体系
- Prompt A/B 平台
- Prompt 缓存平台

---

## 8. 文档维护规则（强约束）

本文件属于 `app/prompts/` 模块的治理模板资产。
后续任何更新，必须严格遵守以下规则：

### 8.1 基线规则
- 必须以当前文件内容为基线进行增量更新
- 不涉及变动的内容不得改写
- 未经明确确认，不得重写文件整体风格

### 8.2 冻结规则
未经明确确认，不得擅自改变以下内容：

- 布局
- 排版
- 标题层级
- 写法
- 风格
- 章节顺序

### 8.3 允许的修改范围
允许的修改仅包括：

1. 在原有章节内补充当前阶段内容
2. 新增当前阶段确实需要的新章节
3. 更新日期、阶段、默认基线等必要信息
4. 删除已明确确认废弃且必须移除的旧约束

### 8.4 禁止事项
禁止：

1. 把原文档整体改写成另一种风格
2. 把模块文档从“模块治理文件”改写成“泛项目说明书”
3. 每次更新都擅自改变标题层级与章节结构
4. 未经确认新增大段不属于本模块职责的内容

### 8.5 模板升级规则
如果未来需要升级 `app/prompts/AGENTS.md` 的模板，必须先明确说明这是一次“模板升级”，并在确认后再统一应用。
在未确认是“模板升级”前，默认只允许做增量更新，不允许重写模板。

---

## 9. 修改规则

1. 新增 Prompt 优先放在模板目录中，而不是 service 中硬编码
2. 模板命名必须体现业务场景，而不是体现临时实现
3. 模板变量必须清晰、稳定、可理解
4. registry 中的公开名称应尽量稳定
5. renderer 不要耦合具体业务流程
6. 模板中不要嵌入与 provider 强绑定的传输协议细节
7. 不允许把 retrieval、context、tool orchestration 逻辑写入 Prompt 层
8. 不允许把当前不存在的 Prompt 版本体系写成已落地能力

---

## 10. Code Review 清单

1. Prompt 是否真正沉淀为资产？
2. 是否还有大量 prompt 硬编码散落在其他层？
3. 是否把业务流程逻辑误塞进模板或 renderer？
4. 模板命名是否清晰？
5. registry 名称是否稳定？
6. renderer 行为是否可理解？
7. 模板变量是否清晰、是否容易缺参或错参？
8. 是否便于新增模板、便于多场景扩展？
9. 本次文档更新是否遵守了“文档维护规则”？
10. 是否保持了原有布局、排版、标题层级、写法和风格？

---

## 11. 测试要求

至少覆盖：

1. 模板查找成功路径
2. 未知模板失败路径
3. 渲染结果基本断言
4. 基础变量替换路径
5. 默认 chat 模板可用性
6. `PromptService.build_messages` / `build_chat_messages` 基础路径

---

## 12. 一句话总结

`app/prompts/` 在当前代码基线中是系统的 Prompt 资产中心，当前以显式 registry、基础 renderer 与默认 system prompt 模板构成最小可用闭环，而不是承担应用主流程逻辑，并在后续更新中严格遵守模块文档的模板冻结规则。
