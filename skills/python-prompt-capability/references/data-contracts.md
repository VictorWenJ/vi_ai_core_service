# data-contracts.md

## 1. 目的

本文件用于说明 `app/prompts/` 中核心对象的最小契约要求。

---

## 2. template_id

必须满足：

- 全局可读
- 场景明确
- 稳定可追踪

例如：
- `chat.default_system`

---

## 3. template file

必须满足：

- 位于 `templates/` 目录下
- 文件名可读
- 内容是可维护的 Prompt 文本
- 不混入复杂业务逻辑

---

## 4. registry mapping

必须满足：

- 显式 template_id -> file path 映射
- 失败路径明确
- 错误信息可理解

---

## 5. renderer input / output

必须满足：

- 输入：template_id + variables
- 输出：渲染后的最终 Prompt 文本
- 缺失模板或缺失变量的行为明确

---

## 6. 原则

- Prompt 资产不是随意字符串
- registry 不是隐式路径猜测器
- renderer 不是业务编排器