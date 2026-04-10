# data-contracts.md

## 1. 目的

本文件用于说明 `app/prompts/` 当前核心对象的最小契约要求。

---

## 2. registry contract

当前 registry 至少应能表达：

- 稳定的 `template_id`
- 显式的 template path 映射

---

## 3. renderer contract

当前 renderer 至少应能表达：

- `template_id`
- 可选 `variables`
- 返回渲染后的字符串

---

## 4. template contract

当前默认模板至少包括：

- `templates/chat/default_system.md`

---

## 5. 原则

- 当前不承诺 Prompt 版本化平台
- 当前不承诺 RAG 专用 knowledge block 模板体系
- contract 变更必须同步补测试
