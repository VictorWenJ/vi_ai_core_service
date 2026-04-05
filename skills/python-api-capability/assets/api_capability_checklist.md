# API Skeleton Checklist

> 更新日期：2026-04-06


## 目录与落位

- API 路由模块已创建在 `app/api/` 下。
- 文件命名体现接口职责。
- 没有把 API 代码错误放到 service/provider/context/prompts 目录中。

## 路由职责

- Route handler 足够薄。
- Route handler 只负责接收、校验、标识透传、委托、返回。
- 没有在 route handler 中写复杂业务编排。
- 没有在 route handler 中写 provider 调用细节。

## C 端 AI 产品适配性

- 请求结构已考虑 conversation_id / session_id / request_id 等标识，或已明确预留。
- 若场景需要，已考虑 messages / attachments / multimodal inputs 的入口结构。
- 若场景需要，已考虑 streaming response 的接口形态或预留。
- API 结构没有被写死成只支持一次性纯文本同步返回。

## 依赖边界

- API 层没有直接 import vendor SDK。
- API 层没有直接操作 context store。
- API 层没有直接读取或渲染 prompt 模板。
- 正常业务路径通过 `app/services/` 进入系统主链路。

## 输入输出

- 请求输入有明确校验。
- 响应结构显式且稳定。
- 没有直接返回 raw vendor SDK object。
- 错误语义基本清晰。
- 取消、失败、超时等用户可感知场景有基本语义预留。

## 当前阶段约束

- 没有提前引入当前阶段不需要的重型机制。
- 没有把 API 层写成“大网关”或“万能入口”。
- 新增接口与当前系统阶段匹配。

## 验证与测试

- 存在 health endpoint 作为最小 smoke validation。
- 至少说明了如何运行或验证该 API。
- 若改动影响主链路，已补充或更新测试。
