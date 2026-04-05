# Context Skeleton Checklist

> 更新日期：2026-04-06


## 目录与落位

- Context 相关代码位于 `app/context/` 下。
- 文件命名与目录结构能够体现职责。
- 没有把 context 逻辑错误放到 API、service、provider 或 prompts 层。

## 基础结构

- `models.py` 定义了基础上下文实体。
- `stores/base.py` 定义了清晰、显式的 store interface。
- `stores/in_memory.py` 提供了本地 in-memory 实现。
- `manager.py` 提供了面向上层的统一入口。

## C 端 AI 产品适配性

- 模型设计已考虑 conversation/session/message 级结构，或已清晰预留。
- 对 stateful（服务端持有状态）与 stateless（客户端带历史）模式有清晰承接思路或预留。
- 消息结构没有被写死成仅支持纯文本字符串。
- 若当前阶段需要，已为 attachment / multimodal metadata 预留字段或扩展位。
- 已考虑未来 compaction / summary / token budget hook 的扩展方向。

## 职责边界

- Context 层保持 provider-agnostic。
- Context 层没有直接调用 provider。
- Context 层没有承担 API 接入职责。
- Context 层没有承担业务编排职责。
- Context 层没有承担 prompt 资产管理职责。

## 当前阶段约束

- 没有引入复杂 long-term memory policy。
- 没有引入 retrieval / RAG 逻辑。
- 没有引入数据库、队列或分布式状态系统。
- 没有进行与当前阶段不匹配的过度架构扩张。

## 行为设计

- manager 暴露的操作最小且清晰。
- store 接口容易替换和扩展。
- in-memory 行为轻量、确定、易于理解。
- 没有隐式副作用或难推断状态。

## 验证与测试

- Context skeleton 可以被清晰发现和使用。
- 接口易于扩展。
- 至少具备最小可验证路径。
- 若改动影响上下文主行为，已补充或更新测试。
