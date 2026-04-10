# module-boundaries.md

## 1. 目的

本文件用于说明 `app/prompts/` 与其他模块之间的边界关系。

---

## 2. 与 services 的边界

### prompts 负责
- 模板资产
- registry
- renderer

### services 负责
- 何时选用哪个 Prompt
- 如何注入变量
- 如何与 context / rag / provider 组合

---

## 3. 与 providers 的边界

### prompts 负责
- provider-agnostic 文本模板资产

### providers 负责
- 模型厂商接入
- chat / stream / embedding 能力

### 原则
Prompt 层不绑定 provider transport 细节。

---

## 4. 与 context 的边界

context 负责会话状态与短期记忆；  
prompts 只负责文本资产，不直接访问 context store。

---

## 5. 与 rag 的边界

rag 负责 retrieval 与 knowledge 数据；  
prompts 可被 services 用来承载知识块变量，但不负责 retrieval。

---

## 6. 与 api 的边界

API 不应直接管理 Prompt 资产。  
route handler 不长期持有 Prompt 文本。

---

## 7. 结论

`app/prompts/` 是 Prompt 资产层，不是业务编排层，不是 provider 适配层，也不是知识检索层。