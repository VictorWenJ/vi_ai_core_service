# LLM Provider 测试矩阵

> 更新日期：2026-04-06


## 一、注册与发现

- Provider 已在 registry 中注册。
- 能通过 provider name 正确发现 provider。
- 不存在名称冲突或覆盖错误。
- provider capability 声明可被读取。

---

## 二、配置校验

- 缺失 API Key 时有清晰错误。
- 缺失必要 base URL / model / region 等配置时有清晰错误。
- 非法配置不会导致静默失败。
- provider 初始化行为可预期。

---

## 三、Canonical Request 映射

### 基础字段映射

- provider 字段处理正确。
- model 字段处理正确。
- system instruction / system prompt 映射正确。
- messages / input items 映射正确。
- stream flag 映射正确。
- metadata 透传策略清晰。

### 采样与生成参数

- temperature 转发正确。
- top_p 转发正确。
- max_tokens / max_output_tokens 转发正确。
- 可选 stop / seed / reasoning 参数（若当前支持）行为清晰。

### 多模态输入

- 文本输入映射正确。
- image/file reference 或 attachment metadata 映射正确或有明确限制。
- 不支持的多模态输入会得到明确错误，而不是静默吞掉。

### Tools 与 Structured Output

- tools / function schemas 映射正确。
- tool_choice / mode 映射正确。
- response_format / 结构化输出 参数映射正确。
- 不支持的工具或结构化输出能力有明确失败语义。

---

## 四、Canonical Response 归一化

### 非流式结果

- content 归一化正确。
- provider 字段正确。
- model 字段正确。
- usage 提取正确。
- finish_reason / stop_reason 提取正确。
- metadata 填充策略清晰。
- raw response 是否保留行为明确。

### Tool / Structured Output 结果

- tool call 信息可被归一化提取。
- 结构化输出 结果可被稳定提取。
- 不同厂商差异不会直接泄漏到 service 层主逻辑。

---

## 五、Streaming 归一化

- 能开始流式返回。
- content delta / chunk 归一化正确。
- finish 事件语义清晰。
- usage 若在流末尾提供，提取行为正确。
- 流式中断 / provider 异常可正确上抛。
- 非流式 provider 不会伪装成流式支持。

---

## 六、错误处理

- 缺失 api key/config 有清晰错误。
- 调用异常能被包装为稳定 provider 异常。
- 超时行为清晰。
- 鉴权失败行为清晰。
- 限流 / 配额错误行为清晰。
- 服务端异常行为清晰。
- malformed response 能被检测，而不是进入上层造成脏数据。

---

## 七、边界检查

- 没有把业务编排逻辑写进 provider。
- 没有把 prompt 组织逻辑写进 provider。
- 没有把 context 管理逻辑写进 provider。
- 没有把 fallback / routing 策略写进 provider。

---

## 八、兼容族复用检查

- OpenAI 兼容 provider 优先复用了兼容基类（如果真实兼容）。
- 不兼容的 provider 没有被错误强塞进兼容基类。
- family base 抽象没有掩盖关键协议差异。

---

## 九、最小回归保障

至少应覆盖：

- 1 个成功调用路径
- 1 个配置错误路径
- 1 个响应归一化路径
- 1 个异常包装路径
- 若支持 streaming，则至少 1 个流式路径
- 若支持 tools 或 结构化输出，则至少 1 个相关路径
