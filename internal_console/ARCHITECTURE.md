# ARCHITECTURE.md

## 1. 文件定位
本文件用于描述 `internal_console/` 的总体前端架构、页面模块划分、与后端的调用关系以及当前阶段的边界约束。

---

## 2. 架构目标
`internal_console/` 的目标不是承载核心业务逻辑，而是作为 `vi_ai_core_service` 的可视化操作与调试前端。

其架构目标包括：
- 提供清晰的页面级能力入口
- 通过稳定 API 消费后端能力
- 正确消费 `/chat_stream` SSE 事件
- 将操作、查看、评估、构建四类能力统一在一个内部控制台中
- 保持与后端解耦，不依赖后端内部实现

---

## 3. 总体结构

## 3.1 前端应用结构
建议的前端应用结构应至少包含：

- `pages/`：页面级入口
- `components/`：可复用组件
- `features/`：按领域划分的前端功能模块
- `api/`：后端接口 client
- `stream/`：SSE / streaming 处理逻辑
- `types/`：前端契约类型
- `hooks/`：页面逻辑复用
- `config/`：前端运行配置

## 3.2 页面模块
当前阶段页面模块包括：
1. Chat Playground
2. Knowledge Ingest
3. Chunk / Vector Inspector
4. Evaluation Dashboard
5. Runtime / Config View

---

## 4. 与后端关系

## 4.1 调用边界
前端只能通过 HTTP / SSE 访问后端公开接口。  
前端运行编排与后端编排独立，使用 `internal_console/infra/compose.yaml` 单独部署。  
前端不应：
- 直接访问 Qdrant
- 直接访问后端内部 Python 对象
- 直接依赖后端测试入口
- 直接消费后端内部日志文件作为主数据源

## 4.2 SSE 关系
对于 `/chat_stream`：
- 前端负责订阅与解析事件
- 前端负责根据事件类型更新页面状态
- 前端不负责定义事件协议本身

---

## 5. 页面架构

## 5.1 Chat Playground
职责：
- 发起 `/chat`
- 发起 `/chat_stream`
- 触发 cancel
- 展示内容、citations、metadata、trace 摘要

边界：
- 不实现会话产品逻辑
- 不实现复杂历史会话管理
- 只服务调试与验证

## 5.2 Knowledge Ingest
职责：
- 上传文档
- 触发构建
- 展示构建结果摘要

边界：
- 不实现完整知识运营后台
- 不做复杂批量工作流管理

## 5.3 Chunk / Vector Inspector
职责：
- 查看 document
- 查看 chunk
- 查看 metadata
- 查看 build/version
- 查看基础检索命中信息

边界：
- 不直接成为向量库运维平台
- 不直接操作底层数据库结构

## 5.4 Evaluation Dashboard
职责：
- 触发评估任务
- 查看 retrieval / citation / answer 结果
- 查看失败样本

边界：
- 不做复杂统计分析平台
- 不做长期评估仓库管理系统

## 5.5 Runtime / Config View
职责：
- 查看当前 runtime 摘要
- 查看主要 provider/model/retrieval 参数
- 查看健康状态

边界：
- 第一版优先只读
- 不做复杂配置中心

---

## 6. 前端状态管理原则
当前阶段优先采用轻量状态管理。

原则：
1. 页面局部状态优先本地管理
2. 共享状态只在确有必要时抽离
3. 不过早引入重型全局状态方案
4. SSE 状态与普通请求状态要清晰区分

---

## 7. 类型与契约原则
前端应显式维护 API contract 类型定义。

要求：
- Chat 响应类型明确
- Stream 事件类型明确
- Build 结果类型明确
- Evaluation 结果类型明确
- 不允许大量使用 `any`

如果后端接口变更，应先更新契约类型，再更新页面逻辑。

---

## 8. 错误处理原则
前端必须将错误显式展示到页面，而不是统一吞掉。

至少应区分：
- 普通请求失败
- SSE 连接失败
- stream error 事件
- cancel 后结束
- 后端评估失败
- 构建失败

---

## 9. 当前阶段非目标架构
当前阶段不设计：
- 微前端
- 多前端应用编排
- SSR/SEO 架构
- 复杂离线缓存系统
- 高级实时协作架构

---

## 10. 后续可扩展方向
未来控制台可进一步承接：
- Tool Calling 观察与调试面
- Workflow / Agent 执行路径观察
- 更丰富的构建与评估对比
- 更正式的产品化交互壳

但这些不是当前第一版前端架构目标。
