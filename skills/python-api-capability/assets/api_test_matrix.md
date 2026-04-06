# API Test Matrix

> 更新日期：2026-04-06

## 当前阶段必测项

1. `/health` 成功路径（200）
2. `/chat` 成功路径（200）
3. `/chat` 输入校验失败路径（422/400）
4. service 异常到 HTTP 状态码映射（400/501/502/500）
5. 响应结构稳定性断言（字段集合与类型）

## 当前阶段不测项（仅预留）

1. streaming 实时输出
2. 多模态真实请求
3. tools/function calling 执行链路
4. structured output 真实输出链路

