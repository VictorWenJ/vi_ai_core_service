# PROJECT_PLAN.md

## 1. 文件定位
本文件用于描述 `internal_console/` 的阶段目标、页面范围、交付顺序和验收口径。

`internal_console/` 是 `vi_ai_core_service` 的内部控制台前端，不是正式用户产品前端。

---

## 2. 当前项目目标
当前版本目标不是做一个商业化前端，而是建立一个能支撑后端继续演进的控制台。

核心目标包括：
1. 提升后端开发调试效率
2. 提升 RAG 操作效率
3. 提升 stream / cancel / citations 的可视化测试能力
4. 提升离线构建与评估结果的可见性
5. 为后续正式产品前端提供 API 消费经验与交互参考
6. 通过领域化 API 契约推动前后端交互方式统一

---

## 3. 当前阶段划分

## Phase C1：Console Foundation
目标：
- 初始化前端项目
- 建立前端治理文档
- 建立基础路由、布局、API client、SSE 处理能力
- 接通后端基础健康与配置查看接口

验收：
- 前端项目可独立运行
- 可通过 `internal_console/infra/compose.yaml` 独立 Docker 启动
- 有基础页面壳与导航
- 有统一 API client
- 有基础 SSE 消费能力

---

## Phase C2：Chat Playground
目标：
- 支持 `/chat`
- 支持 `/chat_stream`
- 支持 `/chat_stream_cancel`
- 展示 citations
- 展示 request / trace / metadata 摘要

验收：
- 能直观测试 chat 与 streaming
- 能稳定复现 cancel 场景
- 能看到 completed / cancelled / error 差异
- citations 可见
- 不依赖 Postman 才能调试核心链路

---

## Phase C3：Knowledge Ingest + Inspector
目标：
- 上传知识文档
- 触发离线构建
- 查看构建结果
- 查看 document / chunk / metadata / build 信息

验收：
- 不再需要通过测试类或手改代码触发基本 ingest
- 能看到 chunk 数据与 metadata
- 能看到 build/version 基础信息
- 基础检索命中结果可查看

---

## Phase C4：Evaluation Dashboard
目标：
- 触发 RAG evaluation
- 查看 retrieval / citation / answer 评估结果
- 查看失败样本和汇总结果

验收：
- 能在页面中运行最小评估集
- 能查看 summary 结果
- 能查看失败 case
- 能支持后续回归对比的基本展示

---

## Phase C5：Runtime / Config View
目标：
- 查看当前运行时摘要
- 查看 provider / model / retrieval 关键参数
- 查看后端健康状态与版本摘要

验收：
- 页面能看到当前主要运行状态
- 基础配置不再完全依赖阅读配置文件
- 不要求当前阶段实现复杂动态配置写回

---

## 4. 当前阶段明确不做
在 Internal Console 当前阶段，不做：
- 正式产品前端
- 登录与复杂权限
- 多租户控制台
- 复杂知识运营后台
- Case Workspace
- 工具工作流编排页
- 完整 Agent 观察台
- 多组织配置中心

---

## 5. 与后端阶段协同关系

### 当前后端基线
- 后端已完成 Phase 7 基线，并进入 RAG 持久化控制面升级阶段
- 控制台当前页面应默认服务于持久化后的 knowledge / build / evaluation / runtime 控制面

当前控制台建设基于：
- Phase 6：Knowledge + Citation Layer
- Phase 7：RAG Evaluation + Offline Build Foundation

未来控制台可逐步承接：
- Phase 8：Tool Calling Foundation
- Phase 9：Workflow / Agent Runtime Foundation

但这些页面不属于当前第一版范围。
当前控制台继续要求与后端领域 API 保持一一对应，不单独发明 `*_console` 风格的长期契约命名。

---

## 6. 交付优先级
当前建议按以下顺序交付：

1. Console Foundation
2. Chat Playground
3. Knowledge Ingest
4. Chunk / Vector Inspector
5. Evaluation Dashboard
6. Runtime / Config View

---

## 7. 当前阶段验收标准
当前第一版控制台完成时，至少应满足：

1. 前端项目独立可运行
2. 能通过 Docker 与后端联调
3. Chat Playground 可测试 chat / stream / cancel / citations
4. 能进行知识上传与离线构建触发
5. 能查看 document / chunk / metadata / build 摘要
6. 能运行并查看最小评估结果
7. 能查看当前运行配置摘要
8. 不破坏后端现有 API contract

---

## 8. 后续演进方向
第一版控制台稳定后，后续可考虑：
- Tool Calling 调试面
- Workflow / Agent 路径可视化
- 更细粒度构建历史
- 更丰富的评估对比能力
- 正式产品前端拆分规划
