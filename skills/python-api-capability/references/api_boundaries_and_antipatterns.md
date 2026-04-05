# API 层边界与反模式

> 更新日期：2026-04-06


## 一、边界定义

### API 层负责什么

API 层负责：

- 协议接入
- 请求解析
- 输入校验
- session / conversation 标识承接
- 响应转换
- 调用 service 层
- 返回稳定的 HTTP 语义
- 为 streaming、附件输入、观测和安全钩子预留入口

### Service 层负责什么

Service 层负责：

- 用例级编排
- 串联 prompt / context / provider
- 主链路流程控制
- 业务结果组织

### Provider 层负责什么

Provider 层负责：

- 厂商 SDK / HTTP 适配
- 请求映射
- 响应归一化
- 厂商差异吸收

---

## 二、API 层必须遵守的原则

1. API 是接入层，不是业务主流程层。
2. API 是协议边界，不是厂商适配层。
3. API 应优先面向 C 端 AI 产品常见交互模式设计。
4. API 应尽量薄、稳定、易测，并对 streaming / multimodal / session 化交互有扩展预留。

---

## 三、典型反模式

### 反模式 1：在 route handler 中直接调用 provider SDK client

错误原因：
- 打穿 `api -> services -> providers` 的依赖方向
- 让 API 层直接知道厂商细节
- 后续难以替换 provider 策略

### 反模式 2：在 API 模块中嵌入业务编排逻辑

错误原因：
- API 层膨胀为业务层
- 流程难复用
- 测试难写
- 模块边界失真

### 反模式 3：API endpoint 直接返回 raw vendor SDK object

错误原因：
- 外部响应结构不稳定
- 厂商协议泄漏到系统外部
- 后续无法统一契约

### 反模式 4：在 API 层直接读写 context 或 prompt 资产

错误原因：
- API 层绕过 service 层
- 模块之间耦合失控
- 未来重构成本高

### 反模式 5：只按一次性文本接口设计，忽略会话、流式、多模态扩展

错误原因：
- 不符合主流 C 端 AI 产品形态
- 后续扩展代价高
- API 很快会被推翻重写

---

## 四、验收标准

一个健康的 API 层实现，应具备以下特征：

- 路由足够薄
- service 委托关系清晰
- 输入输出稳定
- 无厂商耦合泄漏
- 对 conversation / session 形态有清晰承接
- 对 streaming / multimodal / attachment 具备扩展意识
- 易于 smoke test 和接口测试

---

## 五、一句话总结

API 层的正确实现方式是：

**只做协议接入与转换，不做底层适配，不做主流程编排，不泄漏厂商细节，并且面向 C 端 AI 产品常见的会话化、流式化、多模态化交互方式做结构预留。**
