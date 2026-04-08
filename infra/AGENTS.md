# infra/AGENTS.md

> 更新日期：2026-04-08

## 1. 文档定位

本文件定义 `infra/` 目录的职责、边界、结构约束、演进方向与审查标准。  
`infra/` 是项目级工程基础设施目录，不属于 `app/` 七层业务分层。

---

## 2. 目录职责

`infra/` 当前负责：

1. 应用镜像构建（`infra/Dockerfile`）
2. app + redis 本地编排（`infra/compose.yaml`）
3. 本地运行说明（`infra/README.md`）

项目级配置由根目录 `.env.example` 统一提供；`infra/` 不再维护重复模板。

---

## 3. 边界约束

`infra/` 可以做：

- Docker/Compose 运行时定义
- 本地联调与演示说明

`infra/` 不可以做：

- 业务逻辑实现
- API/service/context/provider 代码改造
- Prompt/Context 策略实现
- 生产级容器平台设计（Kubernetes/Helm 等）

---

## 4. 配置治理原则

1. 根目录 `.env.example` 是当前阶段唯一配置文件
2. 根目录 `.env.example` 是当前阶段本地与容器统一配置文件
3. `infra/compose.yaml` 读取根目录 `.env.example`，不依赖重复模板文件
4. 当前阶段不再使用 `.env`
5. 当前阶段不处理 API key 安全治理，后续以独立阶段推进

---

## 5. 当前已落地清单（2026-04-08）

1. `infra/Dockerfile`
2. `infra/compose.yaml`
3. `infra/README.md`
4. 根目录 `.env.example`（当前阶段唯一配置文件）

---

## 6. 执行链路（强制）

1. 根目录 `AGENTS.md`
2. 根目录 `PROJECT_PLAN.md`
3. 根目录 `ARCHITECTURE.md`
4. 根目录 `CODE_REVIEW.md`
5. `infra/AGENTS.md`
6. 代码实现
7. review
8. 文档回写

---

## 7. 交付门禁

1. 不得保留与根目录职责重复的 `infra/.env.example`
2. Compose 配置必须与 `app/config.py` 环境变量命名一致
3. 不得在 `app/` 业务代码中硬编码容器编排细节
4. README 必须明确 `.env.example` 与 compose 的关系
5. 不得恢复 `.env` 或引入第二套 env 文件

---

## 8. 一句话总结

`infra/` 负责“如何运行 app + redis”，不负责“如何实现业务”；当前阶段配置统一以根目录 `.env.example` 为唯一来源。
