# data-contracts.md

## 1. 目的

本文件用于说明 `app/chat_runtime/` 当前会消费或产出的核心数据契约。

---

## 2. 输入契约

当前 chat runtime 会直接消费：

- `RuntimeTurnRequest`
- `ChatRequestAssembler` 所需的装配输入
- retrieval 结果与 provider 归一化结果

---

## 3. 输出契约

当前 chat runtime 主要输出：

- 同步路径：`RuntimeTurnResult`
- 流式路径：runtime event dict + 最终 result/trace 收口

---

## 4. workflow contract

`DEFAULT_CHAT_WORKFLOW` 当前必须保证：

- 顺序稳定
- step 名称唯一
- 主数组中不混入 hook 名称

---

## 5. hook contract

当前 hook 相关数据至少包含：

- event_name
- hook_name
- runtime_ctx / payload
- decision（continue / warn / mutate / block）

---

## 6. 原则

- runtime 内部 contract 不直接暴露为 API 对外 contract
- contract 变更必须同步补测试
- 未落地能力不得写入现有 contract
