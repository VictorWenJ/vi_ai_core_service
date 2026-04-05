# Provider 层边界、兼容策略与验收标准

> 更新日期：2026-04-06


## 一、边界定义

### Provider 层负责什么

Provider 层负责：

- 厂商 SDK / HTTP API 适配
- canonical request -> vendor request 映射
- vendor response -> canonical response 归一化
- 流式 chunk / event 归一化
- provider capability 声明
- provider 配置校验
- provider 级错误包装

### Provider 层不负责什么

Provider 层不负责：

- 业务主流程编排
- context 管理
- prompt 模板组织
- tool execution loop
- agent planning
- provider routing / fallback policy
- 用户态业务逻辑

---

## 二、必须遵守的原则

1. Provider 层必须围绕系统内部 canonical contract 设计。
2. Provider 层必须尽量吸收厂商协议差异，不向上层泄漏。
3. Provider 层必须显式说明 capability，不依赖隐式猜测。
4. Provider 层必须面向当前主流 C 端 AI 应用常见能力：
   - streaming
   - multimodal input
   - tools
   - structured output
   - usage extraction
5. Provider 层应尽量保持可替换、可扩展、可测试。
6. provider routing / fallback 一律放在 service 层。

---

## 三、兼容策略

### 1. 优先识别协议族

新增 provider 前，先判断它属于哪个协议族：

- OpenAI-compatible
- OpenAI native style
- Anthropic Messages style
- Gemini content generation style
- other custom style

### 2. 能复用时复用，不能复用时不要硬套

若某 provider 真实兼容现有 family base，则优先复用。  
若只是“看起来像”，但关键字段、流式格式、tools、usage 或 stop reason 语义已有明显差异，则不要强行兼容。

### 3. canonical contract 高于厂商 contract

系统内部 contract 应稳定。  
某个厂商私有字段如确有价值，应进入 metadata 或 raw_response，而不是污染主 contract。

### 4. streaming 兼容必须单独验证

很多 provider 在非流式上看似兼容，但 streaming event 格式、usage 返回时机、finish 语义差异很大。  
streaming 兼容不能只靠非流式成功来判断。

### 5. tools / structured output 兼容必须单独验证

不同 provider 对：

- tools schema
- tool choice
- JSON mode
- strict structured output

支持程度差异明显。  
必须独立验证，不能默认“兼容”。

---

## 四、典型反模式

### 反模式 1：把 provider 写成业务编排层

错误原因：

- provider 层边界失真
- 上层职责被侵蚀
- 后续难替换 provider

### 反模式 2：把 fallback / routing 写进 provider

错误原因：

- provider 自身开始承担全局策略
- service 层失去编排控制权
- 调试与测试复杂度上升

### 反模式 3：把 canonical contract 绑死在某一家厂商 SDK 上

错误原因：

- provider 无法替换
- 上层逻辑被厂商协议污染
- 后续新增 provider 成本暴涨

### 反模式 4：只支持 text chat，忽略 streaming / multimodal / tools / structured output

错误原因：

- 不符合当前主流 C 端 AI 应用后端能力面
- 后续扩展成本很高
- 很快会触发大重构

### 反模式 5：为了复用而强行套 OpenAI-compatible 基类

错误原因：

- 表面复用，实则隐藏兼容风险
- usage / finish_reason / tools / streaming 很容易出现错配
- 测试矩阵会失真

### 反模式 6：把原始厂商响应直接外泄到上层

错误原因：

- 主 contract 不稳定
- 上层开始知道厂商私有细节
- 跨 provider 行为无法统一

---

## 五、验收标准

一个健康的 provider 实现，应具备以下特征：

- 抽象清晰
- 边界清晰
- 可声明 capability
- 可完成 request / response 归一化
- 流式与非流式行为清晰
- 多模态输入支持或预留清晰
- tools / structured output 支持或预留清晰
- 无业务流程逻辑混入
- 无 routing / fallback 逻辑混入
- 可被测试矩阵验证

---

## 六、一句话总结

Provider 层的正确实现方式是：

**把厂商差异收敛在 provider 层内部，以统一 contract、显式 capability、稳定归一化和清晰边界为核心，为主流 C 端 AI 应用常见的 streaming、多模态、tools 与 structured output 能力提供可扩展支撑。**
