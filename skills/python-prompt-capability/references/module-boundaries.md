# module-boundaries.md

## 1. 目的

本文件用于说明 `app/prompts/` 与其他模块之间的边界关系。

---

## 2. 与 services 的边界

services 负责业务编排与消息装配时机；
prompts 负责模板资产、registry 与 renderer。

---

## 3. 与 providers 的边界

providers 保持 prompt-agnostic；
prompts 不感知 provider transport 细节。

---

## 4. 与 context / rag 的边界

context / rag 提供状态或数据；
services 决定是否作为变量注入。
prompts 不直接访问它们的底层实现。

---

## 5. 结论

`app/prompts/` 是 Prompt 资产层，不是业务编排层，也不是当前代码中的 RAG 模板平台。
