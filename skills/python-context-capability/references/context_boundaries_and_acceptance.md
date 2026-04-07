# Context 层边界与验收标准

> 更新日期：2026-04-06


## 一、边界定义

### Context 层负责什么

Context 层负责：

- 表示 conversation / session / turn / message
- 表示短期会话上下文
- 抽象上下文存储接口
- 提供本地基础实现
- 通过 manager 向上层暴露统一访问入口
- 为上下文裁剪、摘要、压缩、token budget、持久化预留扩展点
 - 实现 token‑aware 窗口选择与截断策略、摘要策略的接口和默认实现（短期历史治理）

### Context 层不负责什么

Context 层不负责：

- API 协议接入
- 业务主流程编排
- provider SDK / HTTP 调用
- prompt 模板管理与渲染
- retrieval pipeline
- 当前阶段复杂 persistence / queue / distributed state
- 当前阶段完整长期记忆系统

---

## 二、必须遵守的原则

1. Context 层必须保持 provider-agnostic。
2. Context 层应优先服务于 C 端 AI 对话产品常见的 session/conversation 短期记忆需求。
3. manager、models、stores 三者职责必须清晰。
4. 当前只做 skeleton 与扩展预留，不做过度系统化建设。
5. 与 API / service 的集成在当前阶段应保持最小、低耦合。
6. 应允许未来兼容 stateless 与 stateful 两种会话模式。
7. token‑aware 窗口治理和摘要逻辑必须放在 context policy 层，并通过 provider 抽象调用模型生成摘要，不得在 service 层或 prompt 层实现。

---

## 三、典型反模式

### 反模式 1：在 context 层中直接写 provider 调用逻辑

错误原因：
- 打穿 context 与 provider 的边界
- 让 context 层绑定模型厂商
- 破坏 provider-agnostic 原则

### 反模式 2：在 context 层中提前实现复杂 long-term memory policy

错误原因：
- 超出当前阶段目标
- 使 skeleton 失去轻量性
- 增加不必要的维护成本

### 反模式 3：把持久化、队列、分布式状态在本轮直接引入

错误原因：
- 把基础骨架阶段变成系统集成阶段
- 增加大量当前不需要的基础设施耦合
- 偏离当前项目节奏

### 反模式 4：manager 直接退化成具体 store 实现

错误原因：
- 管理与存储职责混淆
- 后续难以替换 store
- 抽象失去意义

### 反模式 5：把 context 层模型写死成“只有 text messages 列表”

错误原因：
- 不符合主流 C 端 AI 产品的会话形态
- 后续接入附件、多模态、工具结果时需要推翻重写
- 失去扩展性

### 反模式 6：让 context 层承担业务编排职责

 错误原因：
- 模块边界失真
- service 层职责被侵蚀
- 调用链难以维护

### 反模式 7：在 chat/service 层手写 token‑aware / summary 逻辑

错误原因：
- 打乱上下文治理的策略层次
- 使重用性下降
- 减少测试覆盖范围

---

## 四、验收标准

一个健康的 context skeleton，应具备以下特征：

- 模型清晰
- 接口明确
- store 可替换
- manager 入口统一
- 结构轻量
- 行为确定
- 面向 conversation/session 短期记忆场景
- 对多模态与上下文治理具备扩展意识
- 未引入无关架构扩张
 - 支持 token‑aware window selection、token‑aware truncation 和 summary/compaction 策略，并可通过配置调整 token 预算
 - 提供会话重置能力并经过测试验证

---

## 五、一句话总结

Context 层的正确建设方式是：

**先建立面向 C 端 AI 对话产品的最小、清晰、可扩展的 conversation/session 上下文骨架，再在后续阶段逐步增加压缩、摘要、持久化和长期记忆能力，而不是一开始就实现完整 memory platform。**
