# module-boundaries.md

## 1. 目的

本文件用于说明 `app/schemas/` 与其他模块之间的边界关系。

---

## 2. 与 api 的边界

### schemas 负责
- request / response contract
- stream event payload contract
- cancel / reset contract

### api 负责
- 使用这些 contract 承接输入输出
- 不绕过 schema 临时拼字段

---

## 3. 与 services 的边界

### schemas 负责
- 共享数据表达

### services 负责
- 应用编排与业务语义推进

原则：services 消费 contract，不应随意重新定义 contract。

---

## 4. 与 providers 的边界

providers 可有内部 canonical contract，但共享暴露给上层时，应由 schemas 统一收敛为正式共享表达。

---

## 5. 与 rag 的边界

rag 负责 retrieval 与 citation-ready 数据；  
schemas 负责 citations 的共享表达方式。  
rag 内部对象不直接成为外部 contract。

---

## 6. 与 context 的边界

context 负责内部状态；  
schemas 负责必要时对外共享的生命周期或状态表达。  
内部 state model 不等于共享 schema。

---

## 7. 结论

`app/schemas/` 是共享契约层，不是业务编排层，不是状态层，也不是 provider / rag / context 的内部对象目录。