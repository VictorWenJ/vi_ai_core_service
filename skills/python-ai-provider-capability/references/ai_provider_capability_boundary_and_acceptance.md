# AI Provider 层边界与验收标准

## 一、边界定义

### Provider 层负责什么

Provider 层负责：

- 厂商 SDK / HTTP API 适配
- canonical request -> vendor request 映射
- vendor response -> canonical response 归一化
- provider capability 声明
- provider 级配置校验
- provider 级错误包装
- 同步、流式、异步任务、轮询等执行差异处理
- 文件/媒体输入输出的 provider 级适配

### Provider 层不负责什么

Provider 层不负责：

- 业务主流程编排
- prompt 模板管理
- context 管理
- tool execution orchestration
- fallback / routing policy
- Agent planning
- 数据库存储与队列系统
- 用户态业务逻辑

---

## 二、必须遵守的原则

1. Provider 层必须隔离厂商实现细节。
2. Provider 层必须围绕系统内部 canonical contract 设计。
3. Provider 层必须显式描述 capability 与 execution model。
4. Provider 层必须适配主流 C 端 AI 产品常见 provider 形态：
   - 即时返回
   - 流式返回
   - 长任务轮询
   - 文件/媒体输入输出
5. Provider 层必须可替换、可扩展、可测试。
6. routing / fallback 一律放在 service 层。

---

## 三、典型反模式

### 反模式 1：把 provider 写成业务编排层

错误原因：

- 模块边界失真
- service 层职责被侵蚀
- 后续难以替换 provider

### 反模式 2：只按文本同步返回设计所有 provider

错误原因：

- 无法承接图像、视频、音频、embedding 等真实 provider 形态
- 后续扩展成本高
- 很快触发大重构

### 反模式 3：把 task polling、artifact 下载、状态处理硬塞进业务层

错误原因：

- provider 差异泄漏到上层
- service 层开始理解厂商任务模型
- 跨 provider 行为难统一

### 反模式 4：把厂商 SDK 原始对象直接暴露给上层

错误原因：

- 主 contract 不稳定
- 上层被厂商私有协议污染
- 无法保证通用性

### 反模式 5：把 fallback / routing 写进 provider

错误原因：

- provider 自身承担全局策略
- service 层失去编排控制权
- 调试与测试复杂度明显上升

### 反模式 6：为了抽象而抽象，提前构建过重平台

错误原因：

- 当前阶段复杂度过高
- 维护成本上升
- 偏离最小有效演进路径

---

## 四、验收标准

一个健康的通用 AI provider 实现，应具备以下特征：

- 厂商隔离清晰
- 抽象边界清晰
- capability 声明清晰
- execution model 清晰
- request / response 归一化清晰
- 配置外置化
- 错误语义稳定
- 无业务主流程逻辑混入
- 可被测试与验证

---

## 五、一句话总结

通用 AI Provider 层的正确实现方式是：

**把不同类型 AI 厂商能力的协议差异、执行差异与输入输出差异都收敛在 provider 层内部，以统一 contract、显式 capability、清晰 execution model 和稳定错误语义为核心，为主流 C 端 AI 产品后端提供可持续扩展的外部能力接入层。**