# module-boundaries.md

## 1. 目的

本文件用于说明 `tests/` 与其他模块之间的边界关系。

---

## 2. 与 api 的边界

tests 验证 API contract 与 HTTP 行为，  
不实现 route。

---

## 3. 与 services 的边界

tests 验证应用编排语义与主链路回归，  
不实现 service 本身。

---

## 4. 与 context 的边界

tests 验证 lifecycle 与 memory 收口，  
不实现 state 管理逻辑。

---

## 5. 与 rag 的边界

tests 验证 retrieval / citation 路径与降级行为，  
不实现检索能力本身。

---

## 6. 与 providers / prompts / schemas 的边界

tests 验证这些模块的 contract、registry、renderer、canonical result 稳定性，  
不负责实现这些模块。

---

## 7. 结论

`tests/` 是项目级回归保护层，不是业务实现层，也不是临时脚本堆放目录。