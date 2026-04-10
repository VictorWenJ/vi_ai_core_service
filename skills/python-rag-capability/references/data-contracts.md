# data-contracts.md

## 1. 目的

本文件用于说明 `app/rag/` 中核心数据对象的最小契约要求。

---

## 2. KnowledgeDocument

必须能表达：

- 文档身份
- 标题
- 来源类型
- 原始内容
- 来源地址或文件信息
- 适用域信息
- 时效信息
- 扩展 metadata

---

## 3. KnowledgeChunk

必须能表达：

- chunk 身份
- 所属 document
- chunk 文本
- chunk 顺序
- token 数量
- embedding 模型
- metadata

---

## 4. RetrievedChunk

必须能表达：

- chunk 身份
- 文档身份
- chunk 文本
- 相似度分数
- 来源标题
- 来源地址
- 来源类型
- 时效信息
- metadata

---

## 5. Citation

必须能表达：

- citation 身份
- 对应 document / chunk
- 可展示标题
- 可展示 snippet
- 来源地址
- 来源类型
- 更新时间
- 必要 metadata

---

## 6. 原则

- 外部 citation 不等于内部 retrieval 结果全量透传
- 数据对象必须职责单一
- 不允许一个大 dict 混传所有阶段数据