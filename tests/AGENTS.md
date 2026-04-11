# tests/AGENTS.md

> 更新日期：2026-04-12

## 1. 文档定位

本文件定义 `tests/` 的职责、边界、结构约束、开发约束与 review 标准。
当前阶段，本文件临时同时承担该模块的 `AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW` 职责。
执行 tests 相关任务时，必须先读根目录 `AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md`，再读本文件，再根据 skill `skills/python-test-capability/` 执行。

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

`tests/` 是系统的项目级回归保护层。
它负责为同步聊天、流式聊天、上下文工程、Prompt 资产、provider 抽象、API 契约与 request assembly 提供稳定、可重复、可回归的测试保护。

一句话：**tests 层负责“证明当前能力没被改坏”。**

---

## 3. 本模块职责

1. 为同步 chat 主链路提供回归保护
2. 为流式 chat 主链路提供回归保护
3. 为 context lifecycle 与 layered memory 提供回归保护
4. 为 prompts / providers / schemas 等基础模块提供回归保护
5. 为 request assembly 提供回归保护
6. 为错误路径、取消路径、降级路径提供验证
7. 让阶段演进时具备稳定的验收基础
8. 为 RAG benchmark、黄金评估集与离线构建门禁提供测试与数据集支撑

---

## 4. 本模块不负责什么

1. 不负责业务实现本身
2. 不负责 HTTP 路由实现
3. 不负责 provider SDK 接入
4. 不负责 retrieval / chunking / embedding / index 实现
5. 不负责通过测试替代文档治理
6. 不负责用测试掩盖架构边界问题
7. 不负责作为唯一验证方式取代人工 review

---

## 5. 依赖边界

### 允许依赖
- 被测模块
- 测试框架与断言工具
- fake / mock / in-memory 实现
- 必要的测试辅助工具

### 不建议依赖
- 真实外部 provider 服务作为主回归前置
- 真实向量库作为所有测试前置
- 不稳定的外部环境
- 大量与测试目的无关的运行时资源

### 原则
`tests/` 负责验证，不负责实现。
测试应以稳定、可重复、低噪音为优先。

---

## 6. 架构原则

### 6.1 测试要对应架构边界
测试不仅验证“能跑”，还要验证：
- 分层没有被破坏
- 契约没有漂移
- 生命周期语义没有变化
- 当前阶段边界没有被越界扩张

### 6.2 主回归优先使用确定性测试
优先使用：
- unit tests
- integration tests
- fake / in-memory / stub

避免把主回归建立在不稳定的真实外部依赖上。

### 6.3 关键主链路必须有测试保护
至少要保护：
- `/chat`
- `/chat_stream`
- cancel / reset
- lifecycle 收口
- request assembly
- provider / prompt / context 的关键协作面

### 6.4 当前代码中的回归重点
当前代码已实现 retrieval / citation，主回归重点包括：
- started / delta / heartbeat / completed / error / cancelled
- request assembly 顺序与过滤
- context 持久化与 lifecycle
- provider canonical contract
- rag ingestion / retrieval / citation
- retrieval failure degrade
- retrieval / citation / answer benchmark

### 6.5 测试不能掩盖架构问题
如果实现层边界已经错了，不能靠写更多测试来掩盖。

### 6.6 测试基线收敛原则
- 测试默认只保护当前正式 contract，不保护历史迁移接口
- 旧 test / fake / stub / mock 如不适配当前基线，应直接删除或改写
- 不允许长期并存“新旧两套断言/两套接口”

---

## 7. 当前阶段能力声明

当前前置必须保持稳定：

- 同步 chat 主链路测试
- 流式 chat 主链路测试
- context lifecycle 测试
- provider canonical contract 测试
- Prompt 基础资产测试
- API contract 测试
- request assembly 顺序与 trace 测试
- HTTP smoke 测试

当前代码事实补充：

- 当前仓库已包含 retrieval / citation 测试对象
- request assembly 当前测试的是：system -> knowledge -> working memory -> rolling summary -> recent raw -> user
- 流式测试当前覆盖 completed / cancelled 路径、completed citations 与降级行为
- 当前仓库已新增 `test_rag_evaluation.py` 与 `test_rag_offline_build.py`

当前本轮新增（本轮已落地）：

- retrieval / citation / answer 三层 benchmark
- 黄金评估集与标签集校验
- 构建质量门禁测试

当前本轮不要求：

- 大规模性能压测体系
- 完整 E2E 自动化平台
- 混沌工程体系
- 全量真实外部依赖集成测试

---

## 8. 文档维护规则（强约束）

本文件属于 `tests/` 模块的治理模板资产。
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
如果未来需要升级 `tests/AGENTS.md` 的模板，必须先明确说明这是一次“模板升级”，并在确认后再统一应用。
在未确认是“模板升级”前，默认只允许做增量更新，不允许重写模板。

---

## 9. 修改规则

1. 不允许只写 happy path 测试
2. 不允许把所有测试都绑定真实外部依赖
3. 不允许用 fixture / mock 掩盖错误架构边界
4. 不允许把尚未存在的下一阶段测试写成已覆盖事实
5. 不允许忽略 failed / cancelled / timeout / empty result / downgrade 等路径
6. 不允许让 tests 成为项目中最难维护、最不可信的目录
7. 不允许新增仅用于维持历史兼容分支的测试
8. 不允许保留只覆盖旧方法名或旧 response shape 的过时测试
9. 不允许把纯 LLM 合成样本直接当作唯一正式黄金集而不做分层标注

---

## 10. Code Review 清单

1. 当前改动是否有对应测试？
2. 当前测试是否覆盖关键路径，而不是只覆盖形式？
3. 是否保护了同步与流式两条主链路？
4. 是否保护了 completed / failed / cancelled 的关键差异？
5. 是否保护了 request assembly 顺序？
6. 是否保护了 provider / prompt / context 的关键协作面？
7. 是否没有过度依赖真实外部服务？
8. 本次文档更新是否遵守了“文档维护规则”？
9. 是否保持了原有布局、排版、标题层级、写法和风格？

---

## 11. 测试要求

至少覆盖：

1. `/chat` 正常路径
2. `/chat_stream` 正常路径
3. `/chat_stream_cancel` 路径
4. `/chat_reset` 路径
5. context lifecycle 路径
6. request assembly 顺序
7. provider canonical contract 路径
8. Prompt registry / renderer 基础路径
9. config 与 HTTP smoke 基础路径
10. retrieval / citation / degrade 路径
11. benchmark runner、评估数据集 schema 与构建质量门禁路径

---

## 12. 一句话总结

`tests/` 在当前代码基线中是系统的项目级回归保护层，负责以稳定、可重复、可演进的方式验证同步聊天、流式聊天、context lifecycle、API 契约、provider 归一化、request assembly 与 RAG/citation 主链路没有被改坏，并在后续更新中严格遵守模块文档的模板冻结规则。
