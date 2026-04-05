# Prompt Capability Checklist

> 更新日期：2026-04-06


## 目录与落位

- Prompt 模板位于 `app/prompts/templates/` 下。
- 模板目录结构体现产品场景，而不是临时堆放。
- 没有把 Prompt 模板错误放到 API、service、provider、context 目录中。

## 基础结构

- 存在至少一个基础 system 模板。
- registry 能将模板标识映射到明确文件路径。
- renderer 支持基础变量替换。
- 模板加载路径是显式的、可追踪的。

## C 端 AI 产品适配性

- Prompt 结构已考虑 system / scenario / output constraint 等层次，或已明确预留。
- 对 tools / function calling guidance 有清晰扩展位或预留。
- 对 structured output / JSON mode 的提示约束有清晰扩展位或预留。
- 对多模态输入说明有清晰扩展位或预留。
- 对稳定可复用 Prompt 块有缓存友好组织意识或预留。

## 职责边界

- Prompt 资产属于 `app/prompts/`。
- service 层可以调用 registry / renderer，但不应长期持有 Prompt 文件。
- provider 层保持 prompt-agnostic。
- Prompt 层没有承担业务主流程编排。
- Prompt 层没有承担 tool execution loop。

## 当前阶段约束

- 没有引入复杂 prompt orchestration engine。
- 没有引入与 provider 强绑定的渲染逻辑。
- 没有把 Prompt 层膨胀为业务规则引擎。
- 当前复杂度与项目阶段匹配。

## 资产质量

- 模板命名可读、可推断用途。
- 模板变量清晰，不存在大量隐式魔法变量。
- 模板可发现、可测试、可维护。
- Prompt 文本没有在无关层大面积硬编码。

## 验证与测试

- Prompt skeleton 功能可用且可发现。
- 至少具备最小渲染验证路径。
- 若变更影响主 Prompt 行为，已补充或更新测试。
