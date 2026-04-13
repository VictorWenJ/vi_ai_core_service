# app/chat_runtime/AGENTS.md

> 更新日期：2026-04-13

## 1. 文档定位

本文件定义 `app/chat_runtime/` 的职责、边界、结构约束、开发约束与 review 标准。
当前阶段，本文件临时同时承担该模块的 `AGENTS / PROJECT_PLAN / ARCHITECTURE / CODE_REVIEW` 职责。
执行 chat runtime 相关任务时，必须先读根目录 `AGENTS.md`、`PROJECT_PLAN.md`、`ARCHITECTURE.md`、`CODE_REVIEW.md`，再读本文件，再根据 skill `skills/python-chat-runtime-capability/` 执行。

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

`app/chat_runtime/` 是系统的聊天执行骨架层。
它不是通用 Agent Runtime，也不是 Tool Calling 平台；当前阶段它只服务于 `chat` 与 `chat_stream` 两条主链路的统一执行语义收敛。

当前阶段建议围绕以下职责组织：

- `engine.py`
- `models.py`
- `hooks.py`
- `trace.py`
- `workflows/default_chat.py`

---

## 3. 本模块职责

1. 负责 `chat` / `chat_stream` 统一执行骨架
2. 负责 workflow 主数组解释执行
3. 负责 lifecycle hook 与 step hook 调度
4. 统一协调 scope 标准化、retrieval、request assembly、provider invoke、context 收口、trace 收口
5. 提供 `run_sync` 与 `run_stream` 两类稳定入口
6. 为未来 tool calling、model routing、runtime skill 预留接口位

---

## 4. 本模块不负责什么

1. 不负责 HTTP 路由与 SSE 文本序列化
2. 不负责 provider SDK / HTTP 适配细节
3. 不负责 context store 底层实现
4. 不负责 rag 子域内部 parser / chunker / embedding / index 细节
5. 不负责 runtime skill loader 的正式实现
6. 不负责 Tool Calling Runtime
7. 不负责 Agent Runtime / Planner / Executor
8. 不负责前端适配

---

## 5. 依赖边界

### 允许依赖
- `app/context/`
- `app/prompts/`
- `app/providers/`
- `app/rag/`
- `app/schemas/`
- `app/observability/`
- `app/services/request_assembler.py`（当前阶段允许复用唯一装配中枢）

### 禁止依赖
- `app/api/`
- SSE 文本协议实现
- 向量库底层 SDK 在 runtime 主路径直接散落访问
- 未来 Tool Calling / Agent Runtime 未落地模块的伪实现

### 原则
`app/chat_runtime/` 是聊天执行骨架层，不是协议层、不是知识实现层、不是厂商接入层，也不是通用 Agent 平台层。

---

## 6. 架构原则

### 6.1 主 workflow 必须显式声明
主流程必须定义为数组形式，例如：
- `DEFAULT_CHAT_WORKFLOW = [ ... ]`

主 workflow 中只允许放主业务步骤名，不允许混入 lifecycle hook 名称。

### 6.2 hook 必须与主 workflow 分离配置
必须同时支持：
- lifecycle hooks：`event_name -> list[hook_name]`
- step hooks：`before_step:* / after_step:* -> list[hook_name]`

### 6.3 sync / stream 共用同一套业务语义
- `run_sync` 与 `run_stream` 必须共享同一套主流程语义
- stream 只是交付方式不同，不得重新实现另一套业务主链路

### 6.4 request assembly 只能通过唯一中枢完成
`ChatRequestAssembler` 继续是唯一 request assembly 中枢。
chat runtime 可以调用它，但不得绕过它重新定义装配顺序。

### 6.5 hook 只做 lifecycle control，不做主流程替身
hook 可以承担：
- 审计
- trace 补充
- 输入修正
- 阻断
- 后处理

hook 不得承担主步骤替身角色，不得把 workflow 主逻辑塞进 hook。

### 6.6 skill 当前只保留引用位
当前阶段只允许在 workflow 中保留 `skills[]` 引用位，用于声明依赖的 prompt/能力资产。
不得在本轮实现 runtime skill 自动发现、动态装载或执行器系统。

### 6.7 trace 是一等输出
每次执行都必须能统一收口 trace，用于：
- 调试
- 回归定位
- internal console 未来展示

---

## 7. 当前阶段能力声明

当前本轮必须保持稳定：

- `run_sync`
- `run_stream`
- `DEFAULT_CHAT_WORKFLOW`
- `DEFAULT_CHAT_HOOKS`
- `DEFAULT_CHAT_STEP_HOOKS`
- `DEFAULT_CHAT_SKILLS`
- sync / stream 共用主流程语义
- completed 收口与 citations 契约不回退

当前本轮不要求：

- Tool Calling
- policy center
- runtime skill loader
- planner / executor
- multi-agent coordination

---

## 8. 文档维护规则（强约束）

本文件属于 `app/chat_runtime/` 模块的治理模板资产。
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
如果未来需要升级 `app/chat_runtime/AGENTS.md` 的模板，必须先明确说明这是一次“模板升级”，并在确认后再统一应用。
在未确认是“模板升级”前，默认只允许做增量更新，不允许重写模板。

---

## 9. 修改规则

1. 不允许在 workflow 主数组中混入 lifecycle hook 名称
2. 不允许把 step hook 配置写成隐式 if/else 散落在 engine 中
3. 不允许绕过 `ChatRequestAssembler` 重写装配顺序
4. 不允许重新在 runtime 中散落 SSE 文本协议逻辑
5. 不允许本轮借机做 Tool Calling / Agent Runtime
6. `models.py` 中新增 dataclass 字段必须补中文注释
7. `trace.py` 中的默认常量、hook 决策对象、执行态对象都必须有中文注释或说明
8. 不允许让 `run_sync` 与 `run_stream` 形成两套不同主流程

---

## 10. Code Review 清单

1. `app/chat_runtime/` 是否真正承担了统一执行骨架职责？
2. workflow 是否显式、直观、可追踪？
3. hook 是否与主 workflow 边界清晰？
4. `run_sync` 与 `run_stream` 是否共享同一套业务语义？
5. `ChatRequestAssembler` 是否仍是唯一装配中枢？
6. trace 是否统一收口？
7. 本轮是否越界实现了 Tool / Agent / skill loader？
8. 是否保持了原有布局、排版、标题层级、写法和风格？

---

## 11. 测试要求

至少覆盖：

1. workflow step dispatch 测试
2. lifecycle hook 触发测试
3. step hook 触发测试
4. sync path 与 stream path 共语义测试
5. trace 收口测试
6. retrieval degrade 不拖垮主链路测试
7. completed / cancelled / error 收口测试

---

## 12. 一句话总结

`app/chat_runtime/` 在当前阶段的职责，是作为 `vi_ai_core_service` 的聊天执行骨架层，把同步与流式 chat 的共同业务语义从双编排中收拢出来，并用最小 workflow / hook / trace 结构为后续升级留下清晰落点。
