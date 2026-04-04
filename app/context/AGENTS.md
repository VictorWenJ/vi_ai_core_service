# app/context/AGENTS.md

## 1. 文档定位

本文件定义 `app/context/` 目录的职责、边界、结构约束、演进方向与代码审查标准。

当前阶段，本文件临时同时承担该模块的：

- AGENTS.md
- PROJECT_PLAN.md
- ARCHITECTURE.md
- CODE_REVIEW.md

功能。

本文件只约束上下文管理层。

---

## 2. 模块定位

`app/context/` 是系统的 **上下文管理层**。

它负责描述、组织、存取和管理模型调用所需的会话上下文与消息历史。

当前目录下已有文件：

- `manager.py`
- `models.py`
- `stores/base.py`
- `stores/in_memory.py`
- `__init__.py`

---

## 3. 本层职责

上下文管理层负责：

1. 定义上下文相关的数据表示
2. 管理消息历史与会话上下文
3. 提供统一的上下文访问接口
4. 抽象上下文存储后端
5. 支撑应用编排层获取与更新上下文
6. 为未来上下文裁剪、总结、窗口管理提供承接点

一句话：**context 层负责“对话历史怎么表示、怎么取、怎么存、怎么管理”。**

---

## 4. 本层不负责什么

本层不负责：

1. 不负责 HTTP 接入
2. 不负责 provider API 调用
3. 不负责 prompt 资产管理
4. 不负责具体业务流程编排
5. 不负责将模板文本与上下文拼装成最终 prompt
6. 不负责把某种具体存储实现直接耦合到上层

---

## 5. 依赖边界

### 允许依赖

`app/context/` 可以依赖：

- 标准库
- 极少量通用基础能力
- 自身子模块

### 不建议依赖

`app/context/` 不应常规依赖：

- `app/api/`
- `app/services/`
- `app/providers/`
- `app/prompts/`

说明：

- context 应尽量保持为独立能力模块
- 上层可以调用 context，但 context 不应反向感知上层业务流程

---

## 6. 当前结构约定

建议将当前目录理解为：

- `models.py`
  - 定义上下文相关模型
- `manager.py`
  - 提供面向上层的上下文管理入口
- `stores/base.py`
  - 定义上下文存储抽象
- `stores/in_memory.py`
  - 提供内存版上下文存储实现

后续如果增加持久化存储，可新增：

- `stores/redis_store.py`
- `stores/db_store.py`

但必须保持 `base.py` 抽象稳定，不允许上层与具体 store 强耦合。

---

## 7. 设计原则

### 7.1 管理与存储分离

- manager 负责管理逻辑
- store 负责存取实现

不要把管理策略和具体存储实现混成一层。

### 7.2 上下文模型要清晰

上下文相关模型必须足够明确，避免出现：

- 历史消息结构混乱
- 不同模块各自维护一套上下文格式
- 无法判断哪些字段是系统字段、哪些字段是业务字段

### 7.3 存储可替换

当前可以是内存实现，但整体设计必须允许未来切换为：

- Redis
- 数据库
- 外部 session service

### 7.4 为未来上下文治理留接口

未来可能增加：

- 消息窗口裁剪
- token budget 控制
- 历史摘要
- 长短期记忆分离

当前设计不得阻碍这些演进。

---

## 8. 当前阶段演进计划

本层当前目标：

1. 保持基础上下文模型清晰
2. 保持 manager 与 store 抽象分离
3. 提供最小可用的上下文获取与更新能力
4. 避免把复杂“记忆系统”提前塞进当前项目

### 当前阶段能力声明（强约束）

- 本阶段已实现并验收：
  - manager/store 抽象
  - in-memory 最小上下文读写能力
  - 对单轮主链路的基础上下文承接
- 本阶段仅预留，不要求落地：
  - context persistence（生产级持久化）
  - summary/compaction/token-aware 窗口治理
  - 复杂会话生命周期治理

后续演进方向：

1. 上下文窗口裁剪策略
2. token 感知的上下文控制
3. 历史消息摘要
4. 持久化 store
5. session 生命周期治理
6. 多租户或多会话隔离能力

---

## 9. 修改规则

修改 `app/context/` 时必须遵守：

1. 不要让上层直接依赖具体 store 实现
2. 不要在 context 层写业务流程编排
3. 不要在 context 层写 provider 相关逻辑
4. 不要在不同地方重复定义上下文数据结构
5. 新增字段或模型时，要评估兼容性与迁移影响
6. 如果引入新 store，必须先抽象接口再落实现

---

## 10. Code Review 清单

评审 `app/context/` 代码时，重点检查：

### 边界

- 是否仍然是上下文层，而不是 service 层
- 是否把业务编排逻辑塞进 manager
- 是否把 provider/prompt 逻辑塞进 context

### 抽象质量

- manager 和 store 是否职责清晰
- store 抽象是否稳定
- 是否出现直接绑定某个具体后端的写法

### 数据模型

- 上下文模型是否清晰
- 历史消息格式是否一致
- 是否存在隐式字段或难以理解的状态

### 可扩展性

- 是否支持未来增加新 store
- 是否支持未来增加裁剪/摘要逻辑
- 是否避免后续重构成本过高

---

## 11. 测试要求

上下文层建议至少覆盖：

1. 基础上下文读写
2. manager 与 store 的协作行为
3. in-memory store 的基本正确性
4. 空上下文场景
5. 多条消息追加场景
6. 异常或非法输入场景

---

## 12. 禁止事项

以下做法应避免：

- manager 直接写成具体存储实现
- 上层绕过 manager 直接操作 store 成为常态
- 在 context 层拼接 prompt
- 在 context 层发起模型调用
- 多个模块维护不一致的历史消息结构

---

## 13. 一句话总结

`app/context/` 是系统的上下文能力模块，负责 **上下文的表示、管理、存储抽象与演进承接**，而不是业务流程中心。

---

## 14. 本模块任务执行链路（强制）

Context 类任务必须按以下顺序执行：

1. 先读根目录四文档
2. 再读本文件
3. 再执行 `skills/python-context-capability/SKILL.md` 与其 checklist/reference
4. 再改 `app/context/` 代码
5. 再按根 `CODE_REVIEW.md` + 本文件 + skill checklist 自审
6. 若上下文模型/边界事实变化，回写文档

---

## 15. 本模块交付门禁（新增）

- 发现 context 层承担 provider/API/service 主流程职责时必须先整改
- 变更 manager/store/models 契约时必须补充或更新测试
- 未通过 `python-context-capability` checklist，不视为完成
