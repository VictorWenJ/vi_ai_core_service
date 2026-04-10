# SKILL.md

> skill_name: python-llm-provider-capability
> module_scope: app/providers/
> status: active
> last_updated: 2026-04-10

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `app/providers/` 模块中进行模型与厂商接入层的设计、实现、测试与增量演进。

本 skill 的目标不是生成“泛化的大模型调用示例”，而是约束在本项目文档治理体系下，按当前仓库真实代码结构实现：

- chat completion provider
- stream completion provider
- canonical response / canonical chunk
- provider config / registry / maturity 管理

---

## 2. Skill 适用范围

本 skill 适用于以下类型的工作：

1. `base.py`
2. `openai_compatible_base.py`
3. `openai_provider.py`
4. `deepseek_provider.py`
5. 脚手架 provider
6. `registry.py`
7. provider 相关测试

---

## 3. Skill 不适用范围

本 skill 不用于以下工作：

1. API 路由设计
2. chat 主链路编排
3. context state 管理
4. retrieval / chunking / index 实现
5. citation 生成
6. request assembly
7. retrieval / citation 业务编排
8. 长期记忆平台
9. 审批流
10. Case Workspace

如任务超出上述边界，应转交对应模块 skill 处理。

---

## 4. 本 skill 的核心原则

### 4.1 provider 是能力接入层，不是业务层
provider 负责调用厂商、归一化返回、映射错误；
不负责业务编排、生命周期推进、retrieval 或 citation。

### 4.2 canonical contract 优先
厂商差异必须尽量在 provider 层内部收敛，向上层暴露统一结构。

### 4.3 streaming 与 non-streaming 一致性
同一 provider 在流式与非流式场景下都必须有稳定 contract。

### 4.4 embedding 通过独立抽象落地
当前代码已通过独立 embedding provider 抽象落地，不污染 `BaseLLMProvider`。

### 4.5 成熟度显式化
`ProviderRegistry` 当前通过 `implemented / scaffolded` 描述 Provider 成熟度。
文档、skill 与代码必须保持一致。

---

## 5. 默认阶段基线

当前 skill 默认基线如下：

- chat completion：provider 抽象
- stream completion：provider 抽象
- canonical response / chunk：统一结构
- 已实现 provider：`openai`、`deepseek`
- 脚手架 provider：`gemini`、`doubao`、`tongyi`
- embedding provider：`deterministic`、`openai`

如需变更该基线，必须先更新根目录文档与模块 AGENTS，再进入实现。

---

## 6. 标准执行流程

执行 `app/providers/` 相关任务时，必须遵循以下顺序：

1. 阅读根目录文档
   - `AGENTS.md`
   - `PROJECT_PLAN.md`
   - `ARCHITECTURE.md`
   - `CODE_REVIEW.md`

2. 阅读模块文档
   - `app/providers/AGENTS.md`

3. 阅读本 skill
   - `skills/python-llm-provider-capability/SKILL.md`

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

provider 相关任务，至少应交付以下之一或多项：

1. provider 抽象更新
2. chat provider 实现更新
3. stream provider 实现更新
4. registry / maturity 更新
5. provider 相关测试更新

仅给概念说明、不落代码、不补测试，不视为完成。

---

## 8. 实现约束

### 8.1 抽象约束
必须明确区分：

- chat completion
- stream completion
- provider registry

### 8.2 contract 约束
- 上层不应直接消费厂商原始响应
- canonical non-stream / stream 结构必须清晰
- finish reason、usage、error 应有统一语义

### 8.3 错误映射约束
provider 层负责将厂商错误收敛为项目内统一错误语义。

### 8.4 成熟度约束
实现态与脚手架态必须在代码和文档中一致。

### 8.5 扩展约束
扩展 embedding provider 时，必须继续保持独立抽象边界并同步更新文档与测试。

---

## 9. 与其他模块的协作约束

### 与 services 协作
services 决定何时调用 provider；providers 负责如何调用并返回统一结果。

### 与 api 协作
API 不直接调用厂商 SDK；API 通过 services 间接使用 provider。

### 与 context 协作
context 不直接依赖 provider SDK；provider 也不直接操作 context。

### 与 rag 协作
当前代码中 rag 已落地运行时代码。
provider 不承接 retrieval / citation 职责，只提供 embedding 能力入口。

---

## 10. 测试要求

provider 相关实现至少补以下测试之一或多项：

1. chat provider 基础行为
2. stream provider 基础行为
3. canonical chunk / response 稳定性
4. timeout / error mapping 测试
5. config / registry 测试
6. 实现态 / 脚手架态一致性测试
7. embedding provider 构建与调用测试

---

## 11. Review 要点

提交前至少自查：

1. providers 是否仍为厂商接入层？
2. 是否保持了 canonical contract？
3. 是否没有把 retrieval / context / citation 逻辑写入 provider？
4. provider 成熟度声明是否与代码一致？
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

本 skill 的目标，是确保 `app/providers/` 在当前项目中持续作为模型接入层演进，稳定承接 chat / stream canonical contract、provider registry 与独立 embedding provider 抽象。
