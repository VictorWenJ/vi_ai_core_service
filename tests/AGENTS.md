# tests/AGENTS.md

> 更新日期：2026-04-09

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
4. 维护 Phase 4 layered memory 回归保护
5. 新增 Phase 5 的 streaming / lifecycle / cancel / timeout 回归保护

---

## 4. 当前阶段测试重点

Phase 5 需要补齐并持续维护：

- `/chat/stream` SSE 输出测试
- stream event 顺序测试
- assistant lifecycle 测试
- cancel 路径测试
- failed / cancelled 不进入标准 memory update 的测试
- provider streaming normalization 测试

---

## 5. 修改规则

1. 先确认被测模块归属，再写测试
2. 测试断言必须对齐当前接口契约
3. 改动主链路代码时，必须同步更新对应测试
4. 不允许通过放宽断言掩盖真实回归
5. streaming 改动必须覆盖 API、service、provider、context 至少两层回归

---

## 6. 交付门禁

1. 主链路改动未补测试，不视为完成
2. streaming contract 改动未覆盖 started / delta / completed / error / cancelled，不视为完成
3. failed / cancelled assistant message 过滤规则未覆盖，不视为完成
