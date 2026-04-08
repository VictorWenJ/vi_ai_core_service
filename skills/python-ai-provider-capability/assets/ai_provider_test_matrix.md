# AI Provider 测试矩阵

> 更新日期：2026-04-06

## 当前阶段必测项

1. provider 注册与发现
2. 非流式请求映射与响应归一化
3. 配置错误语义（缺失 key/model）
4. 依赖异常包装语义
5. scaffold provider 的明确失败语义

## 当前阶段不测项（仅预留）

1. streaming 真实事件流
2. 多模态真实请求/响应
3. tools/function calling
4. 结构化输出

