# app/observability/AGENTS.md

> 更新日期：2026-04-12

## 1. 文档定位

本文件定义 `app/observability/` 的职责、边界、结构约束、开发约束与 review 标准。
当前阶段，本文件临时同时承担该模块的 `AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW` 职责。
执行 observability 相关任务时，必须先读根目录 `AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md`，再读本文件，再根据 skill `skills/python-observability-capability/` 执行。

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

`app/observability/` 是系统的可观测性基础设施层。
它负责为同步聊天、流式聊天、上下文工程与 provider 调用提供统一的结构化日志与调试支撑能力。
Phase 7 中，本模块还负责承接 RAG benchmark 与离线构建的事实型日志字段。

当前阶段建议围绕以下职责组织：

- `log_until.py`：`log_report` 与 JSON-safe 序列化辅助
- `__init__.py`：包导出
- 与主链路协作的事实型记录能力

---

## 3. 本模块职责

1. 提供统一的结构化日志能力
2. 提供 JSON-safe 的日志字段序列化能力
3. 为同步 chat 提供可观测性支撑
4. 为流式 chat 提供可观测性支撑
5. 为 context lifecycle 提供可观测性支撑
6. 为 provider / request assembly 等关键步骤提供事实型记录能力
7. 为 benchmark、build 统计与质量门禁提供事实型记录能力
8. 为问题排查、回归验证、联调调试提供事实型记录能力

---

## 4. 本模块不负责什么

1. 不负责 chat 主链路编排
2. 不负责 assistant message lifecycle 状态机推进
3. 不负责 request assembly
4. 不负责 retrieval query 构建
5. 不负责 citation 生成
6. 不负责 context state 更新
7. 不负责 provider 或向量库调用

---

## 5. 依赖边界

### 允许依赖
- 标准库
- 自身模块

### 禁止依赖
- 反向依赖业务层状态机
- 把 observability 写成另一个 services 层
- 在 observability 内直接访问 provider / context / rag 的底层资源

### 原则
`app/observability/` 只做基础设施支撑，不做业务决策。

---

## 6. 架构原则

### 6.1 结构化优先
所有日志必须尽量保持结构化、JSON-safe、可检索。

### 6.2 只记录事实，不记录业务推理
observability 记录的内容应以当前代码真实可得的字段为准，例如：
- request_id
- session_id
- conversation_id
- assistant_message_id
- provider / model
- status / finish_reason / error_code
- context_assembly trace

不记录：
- 随意业务解释
- 不必要的大段正文
- 不可控敏感内容

### 6.3 不能因为日志破坏主链路
不可序列化对象不能直接进入日志。
新增 retrieval / citation 可观测性时，必须继续遵守 JSON-safe 原则。

### 6.4 当前代码中的观测重点
当前代码的观测重点仍然是：
- request / response / stream 生命周期
- context 组装与过滤
- provider 调用结果与错误
- retrieval / citation 相关 trace、降级与失败
- benchmark / offline build 相关统计与失败
- JSON-safe 输出稳定性

### 6.5 observability 是横切支撑，不反向驱动业务
日志帮助定位问题，但不能决定：
- 是否检索
- 是否取消
- 是否进入 memory update
- 是否输出 citation

---

## 7. 当前阶段能力声明

当前本轮必须保持稳定：

- `log_report`
- `_normalize_for_json`
- stdout logger 初始化行为
- 同步 chat、流式 chat、context 组装与 provider 调用相关观测

当前代码事实补充：

- 当前仓库已包含 retrieval / ingestion 专项可观测性实现
- 当前仓库没有 metrics / tracing / alerting 平台
- RAG 观测字段必须继续以真实代码实现为准，不得只写文档字段名

当前本轮新增目标：

- benchmark 运行结果的事实型日志字段
- 离线构建批次、质量门禁与统计的事实型日志字段

当前本轮不要求：

- 完整 tracing 平台
- metrics 平台
- 告警系统
- 统一监控后台

---

## 8. 文档维护规则（强约束）

本文件属于 `app/observability/` 模块的治理模板资产。
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
如果未来需要升级 `app/observability/AGENTS.md` 的模板，必须先明确说明这是一次“模板升级”，并在确认后再统一应用。
在未确认是“模板升级”前，默认只允许做增量更新，不允许重写模板。

---

## 9. 修改规则

1. 不允许把不可 JSON-safe 的对象直接打进日志
2. 不允许在 observability 层实现 chat / stream / retrieval 业务逻辑
3. 不允许输出过量 chunk 原文正文或敏感内容
4. 不允许凭空约定代码中并不存在的 retrieval / citation 字段
5. 不允许用日志替代正式状态存储
6. 不允许把 benchmark 评分逻辑写死在 observability 层

---

## 10. Code Review 清单

1. observability 是否仍然是基础设施层，而不是业务编排层？
2. 同步与流式链路的关键字段是否可观测？
3. `log_report` 与 `_normalize_for_json` 是否仍保持简单、稳定、可复用？
4. 是否保证日志 JSON-safe？
5. 是否没有把大段原始知识文本、敏感数据无控制地写入日志？
6. 新增可观测性是否没有破坏流式主链路？
7. 本次文档更新是否遵守了“文档维护规则”？
8. 是否保持了原有布局、排版、标题层级、写法和风格？

---

## 11. 测试要求

至少覆盖：

1. JSON-safe 序列化
2. request / stream 相关 trace 字段输出
3. dataclass / pydantic / dict / list 等输入归一化
4. 未知复杂对象退化为字符串
5. 流式场景下 observability 不因不可序列化对象崩溃
6. 若后续新增 retrieval 观测字段，再补对应测试
7. retrieval disabled / succeeded / degraded / failed 区分日志路径测试
8. benchmark / build 统计字段输出测试（若本轮新增）

---

## 12. 一句话总结

`app/observability/` 在当前代码基线中是系统的结构化观测基础设施层，当前以 `log_report` 和 JSON-safe 序列化为核心，为同步聊天、流式聊天、上下文生命周期、provider 调用与 retrieval 生命周期提供事实型记录能力，而不参与业务编排与状态决策，并在后续更新中严格遵守模块文档的模板冻结规则。
