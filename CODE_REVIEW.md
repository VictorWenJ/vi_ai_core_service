# CODE_REVIEW.md

> 更新日期：2026-04-09

## 1. 文档定位

本文件定义 `vi_ai_core_service` 的项目级 Code Review 标准。  
本文件只描述适用于整个仓库的通用审查原则、全局质量要求与跨模块检查点，不替代模块内部更细粒度的 review 规则。

---

## 2. Code Review 的目标

本项目中的 Code Review，不只是检查“代码能不能运行”，而是要检查：

1. 是否符合项目分层结构
2. 是否遵守模块边界
3. 是否与项目总体架构一致
4. 是否可维护、可扩展、可测试
5. 是否引入了不必要的耦合和复杂度
6. 是否破坏已有文档治理规则
7. 是否让运行时基础设施治理与业务代码边界混乱

---

## 3. 全局审查原则

### 3.1 先看边界，再看实现
- 代码是否写在正确目录
- 逻辑是否落在正确层/治理域
- 是否存在越层调用
- 是否出现职责混乱

### 3.2 先看结构，再看技巧
更重视：
- 分层是否正确
- 抽象是否合理
- 契约是否稳定
- 命名是否清晰

### 3.3 保守对待会扩大耦合的改动
以下改动应谨慎：
- 上层与下层强绑定
- 多个模块互相知道太多细节
- 某个模块承担了不属于自己的职责
- Schema 被临时需求污染
- 运行时基础设施细节渗入业务主链路

### 3.4 可测试性是硬要求
无法被合理测试的代码，通常说明：
- 抽象有问题
- 职责有问题
- 耦合过高
- 隐式状态过多

---

## 4. 项目级通用审查问题

每次 review，至少要回答以下问题：

1. 这段代码为什么在这个目录，而不是别的目录？
2. 这段逻辑属于哪个层或哪个治理域？
3. 是否破坏当前七层边界？
4. 是否出现跨层绕过？
5. 是否引入循环依赖风险？
6. 是否让未来演进更困难？
7. 是否需要同步更新文档？
8. 是否需要补测试？
9. 注解、提示、说明类文本是否统一使用中文（且语义与原有行为一致）？

---

## 5. 全局边界检查清单

### API 层边界
- API 层是否只做接入、校验、转发、返回
- 是否把业务逻辑塞进了路由层
- 是否保持 HTTP-only 运行约束

### Service 层边界
- Service 是否仍然是编排层
- 是否在 Service 中堆了过多底层适配细节

### Context / Prompt / Provider 边界
- 三个专项能力模块是否仍然职责分离
- 是否出现相互侵入和混写

### Observability 层边界
- 日志能力是否收敛在 `app/observability/`
- 是否存在散落实现
- observability 是否越权承担业务流程或 provider 接入

### Schema 边界
- Schema 是否仍然是契约层
- 是否把流程逻辑或临时厂商特例塞进 schema

### Infra 边界
- Docker / compose / env 样例是否收敛在 `infra/`
- 是否把容器编排细节写进 `app/` 业务代码
- 是否把 Redis 连接细节散落到 API / service 层
- `infra/` 是否承担了不属于它的业务逻辑

---

## 6. 全局命名与结构标准

审查时应关注：

1. 目录命名是否体现职责
2. 文件命名是否体现能力
3. 类名/函数名是否体现真实用途
4. 不允许大量模糊命名

同时必须检查文本规范：

1. 代码注释、docstring、字段说明、错误提示、文档说明是否为中文
2. 是否新增英文说明文本而未同步中文化
3. 技术标识符仍保持英文，避免误翻译导致语义偏差

---

## 7. 全局依赖审查标准

必须重点检查：

1. 是否新增不合理依赖
2. 是否出现从下层反向依赖上层
3. 是否让模块间关系变成网状耦合
4. 是否出现“为了省事直接跨层调用”
5. 是否绕过共享 contract 直接使用私有结构
6. 是否让 `infra/` 反向影响业务依赖链

---

## 8. 全局抽象审查标准

抽象必须满足至少一个合理理由：

- 消除重复
- 固化稳定接口
- 降低替换成本
- 隔离变化点

如果一个抽象只是“看起来更高级”但没有实际收益，应谨慎引入。

---

## 9. 全局契约审查标准

凡是涉及请求、响应、上下文、provider 结果、prompt 输入变量等契约时，都应检查：

1. 字段是否清晰
2. 命名是否稳定
3. 语义是否明确
4. 是否影响多个层
5. 是否兼容现有调用方

---

## 10. 全局错误处理审查标准

审查时要关注：

1. 错误是否在正确层被处理
2. 错误是否被过早吞掉
3. 错误是否被错误地上抛到不该知道细节的层
4. 错误语义是否清晰
5. 是否保留了必要定位信息

异常日志还应关注：

1. 是否按级别区分 `info` 与 `error`
2. 是否输出敏感凭据
3. 业务 payload 输出策略是否明确
4. request/session/conversation 标识是否结构化输出

---

## 11. 全局配置与扩展性审查标准

涉及配置、provider 切换、目录扩展、新增能力时，应检查：

1. 是否破坏现有可替换性
2. 是否把未来扩展写死在当前实现里
3. 是否留下不合理硬编码
4. 是否会让后续新增模块变得困难
5. 是否把本应属于 `infra/` 的运行配置混进业务配置语义中
6. `ContextPolicyConfig`、`ContextStorageConfig`、`ContextMemoryConfig` 是否职责分离

---

## 12. 全局测试审查标准

每个重要改动都要判断：

1. 是否已有测试覆盖
2. 是否应新增测试
3. 是否破坏现有测试语义
4. 是否新增不可测分支
5. 是否影响核心主链路回归安全

以下改动原则上应补测试：

- 主链路改动
- Provider 行为改动
- Prompt 渲染改动
- Context 行为改动
- Schema 契约改动
- 配置加载改动
- Docker / compose 运行方式改动（至少做最小联调验证）
- 分层短期记忆的 scope / reducer / compaction / request assembly 顺序改动

---

## 13. 何时必须同步更新文档

以下情况发生时，必须同步更新文档：

1. 新增了项目级能力边界
2. 修改了模块职责
3. 修改了依赖方向
4. 新增了新的 `app/` 一级目录
5. 某模块复杂度显著上升
6. 文档已无法准确描述当前代码结构
7. 新增或修改 `infra/` 这类项目级工程基础设施治理域
8. 修改了上下文主作用域、记忆层次、request assembly 顺序或配置职责边界

---

## 14. 常见应拒绝的问题改动

以下类型改动应高度警惕，必要时直接拒绝：

1. 为了快直接跨层调用
2. 在错误目录中落代码
3. 把模块边界打穿
4. 在 API 层堆业务逻辑
5. 把厂商细节泄露到上层
6. 把 Prompt / Context / Provider 逻辑混写
7. 把临时字段污染到共享 schema
8. 没有文档更新、没有测试补充的大改动
9. 在 `app/` 内部散落 Docker / compose / 容器编排逻辑
10. 用 `infra/` 脚本替代业务层契约与配置治理
11. 以 Phase 4 为名偷偷引入向量检索、长期记忆或外部 LLM 二次摘要平台

---

## 15. Review 结论建议表达方式

Review 结论优先从以下几个维度给出：

- 边界是否正确
- 结构是否合理
- 依赖是否健康
- 契约是否稳定
- 测试是否足够
- 文档是否需要同步
- 本地运行方式是否可复现

---

## 16. 一句话总结

本项目的 Code Review 核心不是检查“代码写没写完”，而是检查：  
**它是否仍然属于正确的层/治理域、遵守正确的边界、维持正确的依赖方向，并且没有破坏系统后续演进能力。**

---

## 17. 文档驱动闭环审查门禁

每次 review 必须显式检查以下链路是否成立：

`根目录文档 -> 模块 AGENTS -> 对应 skill -> 代码实现 -> review -> 文档回写`

对于 `infra/` 类任务，当前链路为：

`根目录文档 -> infra/AGENTS.md -> 代码实现 -> review -> 文档回写`

---

## 18. Context Engineering Phase 2 专项审查门禁

Phase 2 已完成主链路，当前应继续保持以下约束：

1. token-aware 逻辑仍在 context policy 层
2. summary 不直接调用外部 LLM
3. `request_assembler.py` 仍是正式装配入口
4. reset 通过 manager/service/API 分层调用
5. trace 字段语义清晰、可测试
6. 不把 Phase 2 包装成长期记忆或 RAG

---

## 19. Context Engineering Phase 3 专项审查门禁

在已落地的**持久化短期记忆（Persistent Session Memory）**上，仍必须持续检查：

### 19.1 边界检查
1. Redis/持久化逻辑是否仅存在于 `app/context/stores/` 内
2. 是否把 Redis client、key 拼接、TTL 控制写进了 `chat_service.py`、`request_assembler.py` 或 API 层
3. `ContextManager` 是否继续作为 façade，而不是被绕过
4. 是否把持久化短期记忆偷换成“长期记忆”或“RAG memory”

### 19.2 契约与配置检查
1. 是否定义了独立的 `ContextStorageConfig`
2. backend=`redis` 时失败语义是否清晰
3. store contract 是否仍稳定，支持 get / append / replace / reset
4. session TTL / conversation reset / namespace 是否语义清晰
5. 是否避免在多个层重复维护 key prefix / 序列化格式

### 19.3 一致性与可恢复性检查
1. response 后 user/assistant 历史写回是否通过统一 manager/store 完成
2. reset session / reset conversation 是否只影响目标范围
3. store 序列化 / 反序列化是否稳定
4. 持久化 store 不可用时是否有明确退化策略

---

## 20. Context Engineering Phase 4 专项审查门禁（新增）

在推进 **分层短期记忆（Layered Short-Term Memory）** 时，必须额外检查：

### 20.1 作用域与模型语义检查
1. 上下文主作用域是否统一为 `(session_id, conversation_id)`
2. 不同 `conversation_id` 是否在同一 `session_id` 下仍能保持严格隔离
3. `ContextWindow.messages` 是否明确只表示 recent raw messages
4. `rolling_summary` 与 `working_memory` 是否作为独立状态层管理，而不是塞回普通 message list

### 20.2 链路与边界检查
1. `request_assembler.py` 是否仍是最终 request assembly 顺序的唯一决定点
2. `context/rendering.py` 是否只负责 provider-agnostic block 渲染，而不决定最终顺序
3. `working_memory reducer` 是否留在 `app/context/`，而不是塞进 service / API 层
4. Redis/store 私有细节是否仍未泄漏到 service / API
5. 是否把 Phase 4 偷换成长期记忆 / semantic recall / RAG

### 20.3 算法与实现范围检查
1. rolling summary 是否仍保持确定性、可测试、无外部 LLM 二次调用
2. working memory reducer 是否以高置信度规则为主，而不是不可控的隐式推理黑盒
3. recent raw compaction 是否优先保留最近消息
4. 是否保留最小可解释性，不引入过重策略引擎

### 20.4 配置与契约检查
1. 是否定义了独立的 `ContextMemoryConfig`
2. `ContextMemoryConfig` 是否与 `ContextPolicyConfig` / `ContextStorageConfig` 清晰分离
3. recent raw budget / rolling summary limit / working memory item limit 是否集中配置
4. store 编解码版本与 schema 是否清晰、稳定、可迁移

### 20.5 request assembly 检查
必须检查最终顺序是否为：

1. system prompt
2. working memory block
3. rolling summary block
4. recent raw messages
5. current user input

若任一实现绕过该顺序，原则上应退回整改。

### 20.6 trace / observability 检查
1. 是否能从 trace 中定位当前 scope
2. 是否能看到 recent raw 保留数、compaction 是否触发、summary 是否存在
3. 是否能看到 working memory 的字段命中情况
4. 是否保持日志语义可读且不泄漏敏感信息

### 20.7 测试检查
以下改动原则上必须补测试：
- 同一 session 下不同 conversation 的隔离行为
- reset_conversation / reset_session 的 Phase 4 语义
- recent raw 超预算后的 compaction 行为
- rolling summary 持久化与再次读取
- working memory reducer 的去重、更新与空输入行为
- `request_assembler` 的固定顺序与缺省层优雅跳过行为
- in-memory / redis store 在 layered memory 上的一致性

### 20.8 直接拒绝条件
以下实现应直接拒绝：
- 在 API/service 层直接访问 Redis
- 把 TTL / key prefix / scope 规则写死在多个文件中
- 以“working memory”为名直接接入向量数据库或长期记忆
- 为 summary / memory extraction 新增外部 LLM 调用而无明确阶段批准
- 没有测试就修改 `ContextWindow` / store contract / request assembly 顺序

---

## 21. Infra / Docker / Compose 专项审查门禁

在推进 `infra/` 目录与 Docker / compose 本地联调能力时，必须额外检查：

### 21.1 边界检查
1. Dockerfile / compose / env 样例是否收敛在 `infra/`
2. 是否把容器编排逻辑写进 `app/` 业务代码
3. 是否让业务层依赖容器名称或 compose 结构
4. 是否把“本地联调方式”误写成“业务层默认逻辑”

### 21.2 配置与运行方式检查
1. app 与 redis 的容器职责是否清晰
2. 环境变量来源是否明确
3. compose 中的端口、卷、网络、依赖关系是否清晰
4. 是否提供并统一使用根目录 `.env.example` 作为唯一配置文件
5. 是否有健康检查或最小可观测启动方式
6. 是否仍残留 `.env` 旧模式说明或双轨配置逻辑

### 21.3 直接拒绝条件
以下实现应直接拒绝：
- 在业务代码里硬编码 Docker 容器名
- 为了容器化而改坏本地非容器运行能力
- 在 `infra/` 中堆业务脚本
- 没有文档说明的 Docker / compose 改动

### 21.4 当前范围声明
1. 本轮仅审“配置统一、运行方式统一、文档与代码一致”。
2. 本轮不处理 API key 安全治理，不在本轮引入密钥治理设计结论。
