# tests/AGENTS.md

> 更新日期：2026-04-07

## 1. 文档定位

本文件定义 `tests/` 的职责、边界、结构约束与交付门禁。  
本文件只约束测试层，不替代根目录治理文档或模块 AGENTS。

---

## 2. 模块定位

`tests/` 是仓库级回归保护层，目标是验证“当前代码事实”是否稳定可回归。

---

## 3. 本层职责

1. 覆盖主链路成功/失败路径
2. 覆盖配置、API、service、provider、prompt、context 的最小事实
3. 及时暴露文档与代码、接口与调用方之间的漂移

---

## 4. 本层不负责什么

1. 不负责实现业务逻辑
2. 不负责替代模块边界治理
3. 不为未实现能力编造“未来测试”

---

## 5. 当前阶段能力声明（与代码一致）

- 已有测试文件：
  - `test_api_routes.py`
  - `test_config.py`
  - `test_context_manager.py`
  - `test_context_policies.py`
  - `test_llm_service.py`
  - `test_prompt_service.py`
  - `test_provider_normalization.py`
  - `test_request_assembler.py`
  - `integration/test_http_smoke.py`
- 当前无独立 `test_observability.py`（已移除）

---

## 6. 修改规则

1. 先确认被测模块归属，再写测试。
2. 测试断言必须对齐当前接口契约（例如 `/chat` 请求字段当前为 `user_prompt`）。
3. 改动主链路代码时，必须同步更新对应测试。
4. 不允许通过放宽断言掩盖真实回归。

---

## 7. Code Review 清单

1. 是否覆盖关键成功与错误路径
2. 测试命名是否准确表达行为语义
3. mock 是否必要且不过度
4. 是否验证了错误映射与边界语义
5. 是否出现“测试与真实接口契约不一致”

---

## 8. 执行链路（强制）

1. 根目录四文档
2. 本文件
3. 对应模块 AGENTS 与对应 skill
4. 修改测试
5. 自审与文档回写

---

## 9. 交付门禁

1. 主链路改动未补测试，不视为完成。
2. 测试与当前接口契约不一致，不视为完成。
3. 只改代码不改测试，或只改测试不核对代码事实，不视为完成。
