# AGENTS.md

## 1. 文件定位
本文件用于约束 `internal_console/` 前端项目的协作方式、实现边界、开发原则与文档维护规则。

`internal_console/` 是 `vi_ai_core_service` 的内部控制台前端，不是正式的用户产品前端。  
它的主要职责是为当前 AI Core Service 提供可视化的开发调试面、RAG 操作面、评估查看面和运行状态查看面。

---

## 2. 项目定位

### 2.1 当前定位
`internal_console/` 当前是一个 **Internal Console / Dev Console / Ops Console**。

它服务于以下目标：
- 测试 `/chat` 与 `/chat_stream`
- 测试 stream cancel 行为
- 触发知识导入与离线构建
- 查看 document / chunk / metadata / build 信息
- 运行和查看 RAG evaluation
- 查看当前运行时配置与系统状态

### 2.2 非目标
当前阶段 `internal_console/` 明确不是：
- 正式用户产品前端
- 商业化 UI 产品
- 多角色复杂权限系统
- 知识运营后台完整版
- Case Workspace
- 完整 Agent 控制台

---

## 3. 与后端项目的关系

### 3.1 代码关系
`internal_console/` 与 `vi_ai_core_service` 属于同一仓库下的两个独立应用：
- 后端：`vi_ai_core_service`
- 前端：`internal_console`

### 3.2 部署关系
前端与后端应作为独立 Docker 服务运行，通过本地 HTTP / SSE 接口交互。
前端 Docker 配置固定落在 `internal_console/infra/`，由 `internal_console/infra/compose.yaml` 独立编排。

### 3.3 依赖边界
前端只能依赖：
- 后端公开 API contract
- SSE 事件 contract
- 必要的静态配置摘要接口

前端不得直接依赖：
- 后端 Python 内部模块
- Qdrant 内部实现
- 后端测试脚本
- 后端内部临时对象结构

---

## 4. 当前阶段核心页面范围
当前版本只允许围绕以下页面建设：

1. Chat Playground
2. Knowledge Ingest
3. Chunk / Vector Inspector
4. Evaluation Dashboard
5. Runtime / Config View

未经明确确认，不要擅自扩展到：
- 正式会话管理产品页
- 用户侧工作台
- 多租户后台
- 多步骤 Agent 编排 UI
- 高级审批流界面

---

## 5. 开发原则

### 5.1 前端是操作面，不是新业务中台
前端当前只负责：
- 展示
- 调用
- 触发
- 查看
- 调试

不负责承载后端核心业务逻辑。

### 5.2 API-first
所有前端能力必须建立在明确后端 API 之上。  
不要在前端硬编码后端内部规则来“模拟”后端行为。
控制台消费的后端接口必须按领域命名（如 `knowledge` / `evaluation` / `runtime`），而不是按消费者命名。

### 5.3 页面优先清晰与可用，不优先炫技
当前版本优先：
- 操作清晰
- 状态可见
- 错误可见
- 请求可追踪
- SSE 行为可观察

不要优先追求：
- 复杂动画
- 复杂视觉包装
- 过度组件抽象
- 过度状态管理

### 5.4 控制台前端优先工程效率
允许视觉风格简洁，但不允许：
- 页面结构混乱
- 状态不可追踪
- 调试信息不可见
- 错误吞掉不展示

---

## 6. 技术与结构原则

### 6.1 技术栈建议
- React
- TypeScript
- Vite

### 6.2 目录结构原则
前端项目至少应体现：
- 页面层
- 组件层
- API client 层
- SSE / stream 处理层
- 类型定义层
- 配置层

### 6.3 状态管理原则
当前优先轻量方案。  
没有明确复杂度前，不要过早引入重型状态管理框架。

### 6.4 SSE 处理原则
对于 `/chat_stream`，前端必须明确区分：
- started
- delta
- heartbeat
- completed
- cancelled
- error

不要把所有事件简单当作“文本拼接流”。

---

## 7. 与后端契约协作原则

### 7.1 契约优先
如果页面需要的后端能力当前不存在，应新增后端 API。  
不要通过前端绕开后端边界。
前端类型、API client 与页面路由应以后端领域 schema 与领域 URL 为 source of truth。

### 7.2 错误展示必须保留语义
前端不能把所有错误都统一显示成“请求失败”。  
应尽量保留：
- HTTP 状态
- 错误消息
- stream error 事件
- cancel 状态

### 7.3 调试信息要可见
对于 Chat Playground、Build、Eval 等页面，前端应尽量保留：
- request id
- trace / metadata 摘要
- latency
- citations
- build result
- evaluation result

---

## 8. 当前阶段明确不做
当前阶段不要做：
- 用户登录系统
- 复杂 RBAC
- 正式会话产品页
- 移动端适配优先
- 多组织隔离
- 多语言国际化
- 高级主题系统
- 复杂图表平台
- 产品级设计系统建设

---

## 9. 文档维护规则

### 9.1 根目录四文档职责
`internal_console/` 目录内也采用四文档治理：
- `AGENTS.md`
- `PROJECT_PLAN.md`
- `ARCHITECTURE.md`
- `CODE_REVIEW.md`

### 9.2 更新规则
后续更新必须遵守：
1. 以当前文件为基线增量更新
2. 不涉及变动的内容不得改写
3. 未经明确确认，不得改变布局、排版、标题层级、写法、风格、章节顺序
4. 除非明确说明是模板升级，否则不得整体重写

---

## 10. 协作要求
在开发 `internal_console/` 时，必须先：
1. 明确当前页面范围
2. 明确所需后端 API
3. 更新前端治理文档
4. 再开始代码实现

禁止跳过边界设计，直接生成一套“看起来很全”的前端。
