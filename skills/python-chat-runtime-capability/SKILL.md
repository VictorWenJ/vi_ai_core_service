# SKILL.md

> skill_name: python-chat-runtime-capability
> module_scope: app/chat_runtime/
> status: active
> last_updated: 2026-04-13

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `app/chat_runtime/` 模块中进行聊天执行骨架层的设计、实现、测试与增量演进。

本 skill 的目标不是生成“通用 Agent Runtime 平台”，而是约束在本项目文档治理体系下，按当前仓库真实阶段实现：

- `chat` / `chat_stream` 统一执行骨架
- workflow 主数组
- lifecycle hooks
- step hooks
- sync / stream 共语义执行
- trace 收口
- skills 引用位预留

---

## 2. Skill 适用范围

本 skill 适用于以下类型的工作：

1. `engine.py`
2. `models.py`
3. `hooks.py`
4. `trace.py`
5. `workflows/default_chat.py`
6. chat runtime 相关测试

---

## 3. Skill 不适用范围

本 skill 不用于以下工作：

1. HTTP 路由与 SSE 文本协议
2. provider SDK 适配
3. context store 底层实现
4. rag 子域内部 parser / chunker / embedding / index 细节
5. Tool Calling Runtime
6. Agent Runtime / Planner / Executor
7. runtime skill loader 正式实现
8. 前端适配
9. 长期记忆平台
10. 审批流 / Case Workspace

如任务超出上述边界，应转交对应模块 skill 处理。

---

## 4. 本 skill 的核心原则

### 4.1 workflow 必须显式
主流程必须显式定义为数组配置，不允许把顺序隐式散落在大函数中。

### 4.2 hook 必须独立配置
lifecycle hook 与 step hook 必须与主 workflow 分离，不允许混成一个数组。

### 4.3 sync / stream 共用同一套业务语义
`run_sync` 与 `run_stream` 共享同一套 chat core 语义；stream 只是交付方式不同。

### 4.4 request assembly 仍由唯一中枢负责
chat runtime 可以调用 `ChatRequestAssembler`，但不得绕过它重新定义装配顺序。

### 4.5 hook 只做 lifecycle control
hook 可以审计、补 trace、修正、阻断，但不得承担主步骤替身角色。

### 4.6 skill 当前只保留引用位
当前阶段只允许 `DEFAULT_CHAT_SKILLS = list[str]` 这类引用位，不实现 runtime skill loader。

### 4.7 trace 是一等能力
每次执行都必须能统一收口 trace。

---

## 5. 默认阶段基线

当前 skill 默认基线如下：

- 模块命名：`app/chat_runtime/`
- workflow 形式：数组
- hook 形式：事件数组 + step 前后事件数组
- sync / stream 两个入口
- skill 形式：引用位预留
- 不做 Tool Calling / Agent Runtime / runtime skill loader

如需变更该基线，必须先更新根目录文档与模块 AGENTS，再进入实现。

---

## 6. 标准执行流程

执行 `app/chat_runtime/` 相关任务时，必须遵循以下顺序：

1. 阅读根目录文档
   - `AGENTS.md`
   - `PROJECT_PLAN.md`
   - `ARCHITECTURE.md`
   - `CODE_REVIEW.md`

2. 阅读模块文档
   - `app/chat_runtime/AGENTS.md`

3. 阅读本 skill
   - `skills/python-chat-runtime-capability/SKILL.md`

4. 按需阅读 assets / references
   - `assets/capability-scope.md`
   - `assets/delivery-workflow.md`
   - `assets/acceptance-checklist.md`
   - `references/module-boundaries.md`
   - `references/data-contracts.md`
   - `references/testing-matrix.md`

5. 明确本轮任务边界
6. 设计最小增量改动
7. 补充测试
8. 自检与回归验证

---

## 7. 标准交付物要求

chat runtime 相关任务，至少应交付以下之一或多项：

1. workflow 配置更新
2. hook 配置更新
3. engine 执行逻辑更新
4. trace 收口更新
5. runtime 模型更新
6. runtime 相关测试更新

仅给概念说明、不落代码、不补测试，不视为完成。

---

## 8. 实现约束

### 8.1 workflow 约束
- 主 workflow 使用数组配置
- 主 workflow 中只放主步骤
- 不允许混入 lifecycle hook 名称

### 8.2 hook 约束
- lifecycle hook 使用事件数组配置
- step hook 使用 `before_step:* / after_step:*` 配置
- hook 只能做 lifecycle control，不替代主流程

### 8.3 sync / stream 约束
- `run_sync` 与 `run_stream` 必须共享同一套业务语义
- stream 只是交付方式不同

### 8.4 依赖约束
chat runtime 可依赖：

- `app/context/`
- `app/prompts/`
- `app/providers/`
- `app/rag/`
- `app/schemas/`
- `app/observability/`
- `app/services/request_assembler.py`

不得直接依赖：

- `app/api/`
- SSE 文本序列化实现
- 未正式进入当前阶段的 Tool / Agent 模块

### 8.5 中文字段注释与默认配置说明约束

1. 本模块中所有 `@dataclass` 定义的结构化对象，必须为每一个字段补充中文注释，说明字段含义。
2. 本模块中所有默认配置常量、默认阈值或默认限制项，必须补充中文注释；涉及 token、chars、seconds、ttl、size、top-k、threshold 等值时，必须明确单位或语义。
3. 上述中文注释属于交付物的一部分。除非字段或常量被明确删除，否则后续改动不得删除、不得改为英文、不得在重构中丢失。
4. 字段或配置项语义变化时，必须同步更新对应中文注释。

---

## 9. 与其他模块的协作约束

### 与 services 协作
services 负责 façade 与交付；chat runtime 负责主执行语义。

### 与 context 协作
context 负责 short-term memory 与 completed 收口；chat runtime 负责决定何时触发。

### 与 prompts 协作
prompts 负责模板资产；chat runtime 只声明 skill/prompt 依赖，并通过既有服务进行装配。

### 与 providers 协作
providers 负责厂商适配与 canonical result；chat runtime 只负责编排调用时机。

### 与 rag 协作
rag 负责 retrieval / knowledge / citations 实现；chat runtime 负责统一编排和降级策略。

---

## 10. 测试要求

至少覆盖：

1. workflow step dispatch 测试
2. lifecycle hook 触发测试
3. step hook 触发测试
4. sync / stream 共语义测试
5. trace 收口测试
6. retrieval degrade 不拖垮主链路测试
7. completed / cancelled / error 收口测试

---

## 11. Review 要点

提交前至少自查：

1. workflow 是否显式、清晰、可追踪？
2. hook 是否与 workflow 边界清晰？
3. sync / stream 是否共享同一套语义？
4. `ChatRequestAssembler` 是否仍是唯一装配中枢？
5. 是否没有提前做 Tool / Agent / runtime skill loader？
6. 是否仍符合模块边界与根文档要求？
