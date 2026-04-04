# Prompt 层边界与验收标准

## 一、边界定义

### Prompt 层负责什么

Prompt 层负责：

- 管理 Prompt 模板资产
- 组织模板目录
- 提供 registry 与 renderer
- 定义不同 Prompt 类型的分层方式
- 为多轮对话、工具调用、结构化输出、多模态输入提供提示层扩展位
- 为未来 Prompt 版本治理、变体管理、缓存友好组织预留空间

### Prompt 层不负责什么

Prompt 层不负责：

- API 协议接入
- provider SDK / HTTP 调用
- 业务主流程编排
- context store 管理
- tool execution loop
- Agent planning
- fallback / routing policy
- 用户态业务规则引擎

---

## 二、必须遵守的原则

1. Prompt 文本应优先沉淀为资产，而不是散落在代码中。
2. Prompt 层应支持分层指令组合，而不是长期依赖单一超长模板。
3. Prompt 层必须保持 provider-agnostic。
4. Prompt 层应面向主流 C 端 AI 产品常见形态：
   - 多轮会话
   - tools
   - structured output
   - multimodal input
   - cache-friendly stable blocks
5. registry 与 renderer 必须保持清晰、显式、易测。
6. 当前阶段只做合理工程化，不做过度平台化。

---

## 三、典型反模式

### 反模式 1：在 service / provider 中长期硬编码 Prompt 文本

错误原因：

- Prompt 资产无法统一治理
- 难以 review、难以版本化、难以测试
- 后续改动影响面不可控

### 反模式 2：把所有要求都塞进一个巨大 system prompt

错误原因：

- 难以维护
- 难以复用
- 难以做场景拆分
- 后续缓存与版本治理困难

### 反模式 3：renderer 变成隐式业务决策引擎

错误原因：

- Prompt 层越权
- 业务流程逻辑被藏进渲染器
- 测试和排查成本上升

### 反模式 4：Prompt 层绑定厂商私有协议

错误原因：

- Prompt 层与 provider 强耦合
- 后续替换 provider 成本高
- 无法保持系统内部语义稳定

### 反模式 5：Prompt 模型只考虑纯文本、忽略 tools / structured output / multimodal

错误原因：

- 不符合当前主流 C 端 AI 产品后端形态
- 后续扩展代价高
- 很快需要推翻重写

### 反模式 6：把 Prompt 层写成复杂规则引擎

错误原因：

- 当前阶段过度设计
- 和 service/application 层边界混乱
- 维护成本明显上升

---

## 四、验收标准

一个健康的 Prompt 层实现，应具备以下特征：

- 资产清晰
- 路径显式
- registry 清晰
- renderer 稳定
- 模板命名合理
- 具备 system / scenario / constraint 分层意识
- 对 tools / structured output / multimodal 有清晰扩展位
- 保持 provider-agnostic
- 当前复杂度与项目阶段匹配

---

## 五、一句话总结

Prompt 层的正确建设方式是：

**把 Prompt 视为长期治理的工程资产，以清晰的目录、显式的 registry、稳定的 renderer 和可扩展的分层提示结构，支撑主流 C 端 AI 产品常见的多轮对话、工具调用、结构化输出和多模态交互场景。**