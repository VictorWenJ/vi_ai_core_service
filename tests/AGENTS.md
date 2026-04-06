# tests/AGENTS.md

> 更新日期：2026-04-06

## 1. 文档定位

本文件定义 `tests/` 目录的职责、边界、结构约束与交付门禁。
本文件只约束测试层实现，不替代根目录治理文档与模块级 `AGENTS.md`。

---

## 2. 模块定位

`tests/` 是仓库级回归保护层，负责验证当前阶段“基础设施 + 单轮非流式主链路”是否持续稳定。

---

## 3. 本层职责

测试层负责：

1. 覆盖主链路的成功与失败路径
2. 覆盖配置、路由、编排、provider 归一化、prompt/context、observability 的最小事实
3. 为代码重构提供回归安全网
4. 通过结构化断言降低行为漂移风险

---

## 4. 本层不负责什么

测试层不负责：

1. 不负责实现业务逻辑
2. 不负责修复架构边界错误（测试只能暴露问题）
3. 不负责替代模块文档治理
4. 不负责为未实现能力写“未来假测试”

---

## 5. 依赖边界

### 允许依赖

- `app/` 下公开模块接口
- 标准测试框架与最小 mock 工具

### 禁止依赖

- 测试层中复制业务实现逻辑
- 测试层直接依赖私有/临时内部细节（非必要）
- 为通过测试而反向修改业务语义

---

## 6. 当前阶段能力声明（强约束）

- 本阶段已实现并要求稳定：
  - `/health`、`/chat` 基础路由行为
  - service 主链路（非流式）
  - provider 基础归一化
  - prompt 渲染与模板查找
  - context manager/store 基础读写
  - observability 基础行为（前缀+`message=<json>`、开关、异常日志、request context）
- 本阶段仅预留，不作为测试通过标准：
  - streaming 真正输出链路
  - 多模态真实处理链路
  - tools/function calling 真实执行
  - structured output 真实能力

---

## 7. 建议结构

当前建议保留：

- `tests/test_api_routes.py`
- `tests/test_llm_service.py`
- `tests/test_provider_normalization.py`
- `tests/test_prompt_service.py`
- `tests/test_context_manager.py`
- `tests/test_config.py`
- `tests/test_observability.py`
- `tests/integration/test_http_smoke.py`（integration skeleton）

---

## 8. 修改规则

1. 先确认被测能力归属模块，再写对应测试
2. 测试描述必须与当前阶段能力一致
3. 不为未实现能力补“伪通过测试”
4. 改动主链路逻辑时必须同步更新测试断言
5. 测试失败时优先判断是代码事实变化还是断言失真

---

## 9. Code Review 清单

1. 测试是否覆盖核心成功/失败路径
2. 测试命名是否表达真实业务语义
3. 是否存在过度 mock 导致失真
4. 是否校验了错误映射与边界语义
5. 是否破坏了现有回归基线

---

## 10. 本模块任务执行链路（强制）

Tests 类任务必须按以下顺序执行：

1. 先读根目录四文档
2. 再读本文件
3. 再按被测模块匹配对应 skill
4. 再落测试改动
5. 再按根 `CODE_REVIEW.md` + 本文件 + 对应 skill checklist 自审
6. 若测试事实变化影响文档，回写对应文档

---

## 11. 本模块交付门禁

- 主链路改动未补回归测试，不视为完成
- 测试与当前阶段能力声明不一致，不视为完成
- 只改代码不改测试（或只改测试不核对代码事实）不视为完成
