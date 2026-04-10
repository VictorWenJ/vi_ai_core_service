# SKILL.md

> skill_name: python-llm-provider-capability  
> module_scope: app/providers/  
> status: active  
> last_updated: 2026-04-10

## 1. Skill 定位

本 skill 用于指导 `vi_ai_core_service` 在 `app/providers/` 模块中进行模型与厂商接入层的设计、实现、测试与增量演进。

本 skill 的目标不是生成“泛化的大模型调用示例”，而是约束在本项目文档治理体系下，按企业级 AI 应用的标准实现：

- chat completion provider
- stream completion provider
- embedding provider
- canonical response / canonical chunk
- provider 配置与错误映射

---

## 2. Skill 适用范围

本 skill 适用于以下类型的工作：

1. provider 抽象设计
2. chat completion provider 实现
3. stream completion provider 实现
4. embedding provider 实现
5. canonical response / chunk 结构
6. provider config / registry / factory
7. 错误映射与超时处理
8. provider 相关测试

---

## 3. Skill 不适用范围

本 skill 不用于以下工作：

1. API 路由设计
2. chat 主链路编排
3. context state 管理
4. retrieval / chunking / index 实现
5. citation 生成
6. request assembly
7. 长期记忆平台
8. 审批流
9. Case Workspace

如任务超出上述边界，应转交对应模块 skill 处理。

---

## 4. 本 skill 的核心原则

### 4.1 provider 是能力接入层，不是业务层
provider 负责：
- 调用厂商
- 归一化返回
- 映射错误
- 输出统一 contract

不负责：
- 业务编排
- 生命周期推进
- retrieval 决策
- citation 生成

### 4.2 canonical contract 优先
所有 provider 的差异都应尽量被吸收到 provider 层内部。  
向上层暴露的应是统一结构。

### 4.3 streaming 与 non-streaming 一致性
同一模型能力在流式与非流式场景下都应有稳定 contract。  
不能让上层到处写 provider-specific 分支。

### 4.4 embedding 是 provider 能力的一部分
Phase 6 后，embedding provider 统一纳入 provider 能力域管理。  
不得额外创建重复 skill 或并行 provider 治理体系。

### 4.5 provider-agnostic 优先
services / rag / api 应尽量不感知厂商差异。  
厂商差异应在 provider 层收敛。

---

## 5. 默认阶段基线

当前 skill 默认基线如下：

- chat completion：provider 抽象
- stream completion：provider 抽象
- embedding：provider 抽象
- canonical response / chunk：统一结构
- 错误映射：统一语义
- 当前 Phase 6 embedding 基线：文本 embedding

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
4. embedding provider 实现更新
5. canonical response / chunk 更新
6. provider config / registry 更新
7. provider 相关测试更新

仅给概念说明、不落代码、不补测试，不视为完成。

---

## 8. 实现约束

### 8.1 抽象约束
必须明确区分：
- chat completion
- stream completion
- embedding

不得把三者随意混在一个无边界类里。

### 8.2 contract 约束
- 上层不应直接消费厂商原始响应
- canonical non-stream / stream / embedding 结构必须清晰
- finish reason、usage、error 应有统一语义

### 8.3 错误映射约束
- provider 层负责将厂商错误收敛为项目内统一错误语义
- 不直接将厂商异常类型泄漏给业务层

### 8.4 embedding 约束
- 当前只要求文本 embedding
- 输出维度与数据类型必须稳定
- embedding 结果需与下游 index 契约兼容

### 8.5 扩展约束
未来可以扩展：
- 多厂商 provider
- 多模态 embedding
- provider fallback  
但当前阶段不要求一次性做完。

---

## 9. 与其他模块的协作约束

### 与 services 协作
services 决定何时调用 provider；providers 负责如何调用并返回统一结果。

### 与 api 协作
API 不直接调用厂商 SDK；API 通过 services 间接使用 provider。

### 与 context 协作
context 不直接依赖 provider SDK；provider 也不直接操作 context。

### 与 rag 协作
rag 可通过 embedding provider 获取向量化能力；provider 不负责 retrieval / citation。

---

## 10. 测试要求

provider 相关实现至少补以下测试之一或多项：

1. chat provider 基础行为
2. stream provider 基础行为
3. canonical chunk / response 稳定性
4. embedding provider 基础行为
5. 维度与数据类型测试
6. timeout / error mapping 测试
7. config / registry 测试

---

## 11. Review 要点

提交前至少自查：

1. providers 是否仍为厂商接入层？
2. 是否保持了 canonical contract？
3. 是否没有把 retrieval / context / citation 逻辑写入 provider？
4. embedding 能力是否正确纳入 provider 域？
5. 是否补了测试？
6. 是否没有破坏流式与非流式主链路？

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

本 skill 的目标，是确保 `app/providers/` 在当前项目中以企业级、可增量演进、可测试、可审查的方式统一承接 chat completion、stream completion 与 embedding 的厂商接入能力，并通过 canonical contract 屏蔽厂商差异，而不是演化成承担业务编排与知识检索职责的模块。