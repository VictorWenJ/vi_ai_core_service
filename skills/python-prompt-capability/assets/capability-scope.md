# capability-scope.md

## 1. 目的

本文件用于说明 `python-prompt-capability` 当前阶段的能力范围，避免 skill 在执行过程中发生边界漂移。

---

## 2. 当前能力范围

当前能力范围限定为：

- Prompt 模板目录
- Prompt 模板文件
- registry
- renderer
- 模板变量渲染
- Prompt 命名与查找规则
- Prompt 资产化收敛
- Prompt 相关测试

---

## 3. 当前不在范围内

当前不在范围内的能力包括：

- API 协议接入
- chat 主流程编排
- provider SDK 调用
- context store 管理
- retrieval / chunking / embedding / index
- tool execution loop
- Agent 规划
- Prompt 平台化系统
- 审批流
- Case Workspace

---

## 4. 当前默认技术基线

- 模板目录：`app/prompts/templates/`
- registry：显式映射
- renderer：基础变量替换
- 默认 chat 模板：`templates/chat/default_system.md`
- provider-agnostic

---

## 5. 使用原则

如果某项需求超出本文件定义的能力范围，应先更新根文档与模块 AGENTS，再更新 skill，不得在实现阶段直接越界扩展。