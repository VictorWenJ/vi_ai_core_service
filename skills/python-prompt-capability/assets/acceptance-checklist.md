# acceptance-checklist.md

## 1. 目的

本文件用于在 `app/prompts/` 相关任务完成后进行验收自检。

---

## 2. 验收清单

### 目录与落位
- [ ] Prompt 模板位于 `app/prompts/templates/` 下
- [ ] 模板目录结构体现业务场景
- [ ] 没有把 Prompt 模板错误放到 API、service、provider、context、rag 中

### 基础结构
- [ ] 存在至少一个基础 system 模板
- [ ] registry 能将模板标识映射到明确文件路径
- [ ] renderer 支持基础变量替换
- [ ] 模板加载路径是显式的、可追踪的

### 边界
- [ ] Prompt 资产属于 `app/prompts/`
- [ ] service 层可以调用 registry / renderer，但不长期持有 Prompt 文件
- [ ] provider 层保持 prompt-agnostic
- [ ] Prompt 层没有承担业务主流程编排
- [ ] Prompt 层没有承担工具执行循环

### 当前阶段约束
- [ ] 没有引入复杂 prompt orchestration engine
- [ ] 没有引入与 provider 强绑定的渲染逻辑
- [ ] 没有把 Prompt 层膨胀为业务规则引擎
- [ ] 当前复杂度与项目阶段匹配

### 资产质量
- [ ] 模板命名可读、可推断用途
- [ ] 模板变量清晰，不存在大量隐式魔法变量
- [ ] Prompt 文本没有在无关层大面积硬编码

### 验证与测试
- [ ] 模板查找可用
- [ ] 基础渲染可用
- [ ] 若变更影响主 Prompt 行为，已补充或更新测试