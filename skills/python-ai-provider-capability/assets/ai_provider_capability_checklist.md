# AI Provider Capability Checklist

> 更新日期：2026-04-06


## 当前阶段使用说明（vi_ai_core_service）

- 当前阶段只要求非流式 LLM provider 主路径稳定。
- checklist 中涉及 streaming、polling、artifact、多模态、tools、structured output 的项，仅在该能力已真实实现时检查。
- 对未实现能力，要求是“明确预留与明确失败语义”，而不是“伪实现”。

## 目录与落位

- Provider 逻辑位于 `app/providers/` 下。
- 文件命名能体现 provider 类型与职责。
- 没有把 provider 代码错误放到 API、service、context、prompts 目录中。

## 抽象与隔离

- 厂商 SDK / HTTP 逻辑被隔离在 provider 层内部。
- service / API 层没有直接依赖厂商 SDK 结构。
- provider 的 capability 声明是显式的。
- provider family / base 复用合理，没有为了复用而强行兼容。

## 执行模型

- 已明确该 provider 是 sync、streaming、async-job 还是 polling 型。
- 若为长任务 provider，task submit / poll / result retrieval 语义清晰。
- 若为流式 provider，流式事件或 chunk 归一化语义清晰。
- 没有把不同执行模型粗暴混成同一种返回形态。

## 输入输出

- canonical request 与 vendor request 映射清晰。
- canonical response 与 vendor response 归一化清晰。
- 若存在文件/媒体输入，输入承接方式清晰。
- 若存在 artifact/file 输出，结果表示方式清晰。
- 不支持的能力会显式报错，而不是静默忽略。

## 配置与错误处理

- API key / base URL / region / timeout / polling config 等已配置化。
- 缺失配置有清晰错误。
- 鉴权失败、限流、超时、厂商异常有清晰错误语义。
- malformed response 能被检测，而不是污染上层。

## 边界约束

- provider 层没有承担业务主流程编排。
- provider 层没有承担 prompt 管理。
- provider 层没有承担 context 管理。
- provider 层没有承担 fallback / routing 策略。

## 当前阶段约束

- 没有引入与当前阶段不匹配的超重 provider 平台。
- 没有混入无关重构。
- 扩展点合理，但不过度设计。

## 验证与测试

- provider 能在既有 service entrypoint 后被调用。
- 核心映射路径可验证。
- 错误路径可验证。
- 若支持 streaming / polling / artifact output，至少有最小验证路径。
