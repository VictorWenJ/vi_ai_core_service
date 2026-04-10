# module-boundaries.md

## 1. 目的

本文件用于说明 `app/providers/` 与其他模块之间的边界关系。

---

## 2. 与 services 的边界

### providers 负责
- 调用厂商
- 输出 canonical result / chunk
- 映射错误
- 维护成熟度与注册入口

### services 负责
- chat / stream 编排
- lifecycle 推进
- cancel / reset 收口

---

## 3. 与 api 的边界

API 不直接调用 provider SDK。
provider 通过 service 间接服务于 API。

---

## 4. 与 context 的边界

context 负责会话状态；providers 不直接操作 context。

---

## 5. 与 rag 的边界

当前代码中 rag 已落地运行时代码。
providers 仍不负责 retrieval / citation。

---

## 6. 结论

`app/providers/` 是模型与厂商接入层，不是业务编排层，也不是知识检索层；embedding 通过独立 provider 抽象在本模块内维护。
