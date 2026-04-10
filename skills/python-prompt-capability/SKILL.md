# SKILL.md

> skill_name: python-prompt-capability
> module_scope: app/prompts/
> status: active
> last_updated: 2026-04-10

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `app/prompts/` 模块中进行 Prompt 资产层的设计、实现、测试与增量演进。

本 skill 的目标不是生成“泛化的 Prompt 示例代码”，而是约束在本项目文档治理体系下，按当前仓库真实代码结构实现：

- Prompt 模板资产管理
- Prompt registry
- Prompt renderer
- 默认 chat system prompt

---

## 2. Skill 适用范围

本 skill 适用于以下类型的工作：

1. Prompt 模板目录结构
2. Prompt 模板文件新增与维护
3. registry 设计与实现
4. renderer 设计与实现
5. Prompt 变量渲染
6. Prompt 命名与查找规则治理
7. Prompt 相关测试

---

## 3. Skill 不适用范围

本 skill 不用于以下工作：

1. API 路由设计
2. chat 主链路编排
3. provider SDK 调用
4. context store 管理
5. retrieval / chunking / embedding / index 实现
6. tool execution loop
7. Agent 规划
8. 审批流
9. Case Workspace

如任务超出上述边界，应转交对应模块 skill 处理。

---

## 4. 本 skill 的核心原则

### 4.1 Prompt 是资产，不是内联文本
需要复用、维护、审查的 Prompt，应优先沉淀为模板资产。

### 4.2 registry 与 renderer 分离
- registry 负责模板查找
- renderer 负责模板渲染

### 4.3 provider-agnostic
Prompt 层必须保持 provider-agnostic，不嵌入厂商私有协议细节。

### 4.4 当前代码只有最小闭环
当前代码仅包含显式模板映射、基础字符串替换 renderer 与默认 system prompt。
未落地能力不得写成默认基线。

### 4.5 复杂逻辑不上模板
复杂业务判断应放在应用编排层或上游准备阶段。

---

## 5. 默认阶段基线

当前 skill 默认基线如下：

- Prompt 资产目录：`app/prompts/templates/`
- registry：显式 `template_id -> file path` 映射
- renderer：基础变量替换
- 默认 chat 模板：`templates/chat/default_system.md`
- 当前不包含版本化 / 平台化体系

如需变更该基线，必须先更新根目录文档与模块 AGENTS，再进入实现。

---

## 6. 标准执行流程

执行 `app/prompts/` 相关任务时，必须遵循以下顺序：

1. 阅读根目录文档
   - `AGENTS.md`
   - `PROJECT_PLAN.md`
   - `ARCHITECTURE.md`
   - `CODE_REVIEW.md`

2. 阅读模块文档
   - `app/prompts/AGENTS.md`

3. 阅读本 skill
   - `skills/python-prompt-capability/SKILL.md`

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

Prompt 相关任务，至少应交付以下之一或多项：

1. 模板文件新增或更新
2. registry 更新
3. renderer 更新
4. Prompt 相关测试更新

仅给概念说明、不落代码、不补测试，不视为完成。

---

## 8. 实现约束

### 8.1 资产化约束
需要复用、维护、审查的 Prompt，应优先沉淀为模板资产。

### 8.2 模板约束
- 模板文件名应可读、可推断
- 模板变量应清晰、稳定
- 模板内容保持可读性

### 8.3 registry 约束
- registry 必须显式
- template_id 命名必须稳定
- 不依赖隐式路径猜测

### 8.4 renderer 约束
- renderer 只负责渲染
- renderer 不负责业务判断
- renderer 当前采用基础字符串替换

### 8.5 Phase 6 约束
当前 Prompt 层尚未因 RAG 引入新的 knowledge block 模板体系。

---

## 9. 与其他模块的协作约束

### 与 services 协作
services 可调用 registry / renderer 获取 Prompt 文本；
prompts 不负责业务编排。

### 与 providers 协作
providers 保持 prompt-agnostic；
prompts 不感知 provider transport 细节。

### 与 context / rag 协作
context 和 rag 提供状态或数据；
services 决定是否作为变量注入，prompts 不直接访问它们的底层实现。

---

## 10. 测试要求

Prompt 相关实现至少补以下测试之一或多项：

1. 模板查找成功路径
2. 未知模板失败路径
3. 基础变量渲染替换
4. 默认 system prompt 可用性
5. `PromptService` 装配路径

---

## 11. Review 要点

提交前至少自查：

1. Prompt 是否真正沉淀为资产？
2. 是否还有大量 prompt 硬编码散落在其他层？
3. registry 与 renderer 是否仍职责清晰？
4. 是否没有把未落地的平台化能力写成已实现事实？
5. 是否补了测试？

---

## 12. 关联文件

- `assets/capability-scope.md`
- `assets/delivery-workflow.md`
- `assets/acceptance-checklist.md`
- `references/module-boundaries.md`
- `references/data-contracts.md`
- `references/testing-matrix.md`

---

## 13. 一句话总结

本 skill 的目标，是确保 `app/prompts/` 在当前项目中持续作为最小可用 Prompt 资产层演进，以显式 registry、基础 renderer 和默认 system prompt 支撑主链路，而不是把尚未存在的 Prompt 平台能力写成当前实现。
