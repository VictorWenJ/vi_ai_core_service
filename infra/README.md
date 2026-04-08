# infra 目录说明

`infra/` 是项目级工程基础设施目录，用于统一管理本地运行、联调和演示方式。  
它不属于 `app/` 七层业务分层，不承载业务代码。

当前目录提供：

- `Dockerfile`：构建 app 运行镜像
- `compose.yaml`：编排 app + redis
- 根目录 `.env.example`：项目级环境变量模板（单一事实来源）

## 1. 前置条件

1. 已安装 Docker Desktop（或等价 Docker + Compose 环境）
2. 当前路径位于仓库根目录 `vi_ai_core_service`

## 2. 启动步骤

1. 在仓库根目录复制环境变量样例：

```powershell
# 直接编辑根目录 .env.example 即可，无需再复制出 .env
```

2. 启动 app + redis：

```powershell
docker compose -f infra/compose.yaml up -d --build
```

3. 查看服务状态：

```powershell
docker compose -f infra/compose.yaml ps
```

## 3. 验证接口

健康检查：

```powershell
curl http://127.0.0.1:8000/health
```

若返回 `{"status":"ok","service":"vi_ai_core_service"}`，说明 app 已启动。

## 4. 查看日志

查看 app 日志：

```powershell
docker compose -f infra/compose.yaml logs -f app
```

查看 redis 日志：

```powershell
docker compose -f infra/compose.yaml logs -f redis
```

## 5. 停止与清理

停止服务：

```powershell
docker compose -f infra/compose.yaml down
```

停止并删除镜像/卷（可选）：

```powershell
docker compose -f infra/compose.yaml down --rmi local --volumes
```

## 6. 角色说明

- `app`：运行 FastAPI HTTP 服务（入口：`app.server:app`）
- `redis`：提供 Phase 3 持久化短期记忆依赖

其中 `infra/compose.yaml` 通过 `env_file: ../.env.example` 读取根目录 `.env.example`。  
`CONTEXT_REDIS_URL=redis://redis:6379/0` 使用 compose 服务名 `redis` 进行容器内网络访问。

## 7. 运行边界

1. 当前方案仅用于本地开发/联调/演示
2. 不代表生产部署方案
3. 不包含 Kubernetes、Helm、生产高可用 Redis 编排
4. `infra/` 不再维护独立的项目级 `.env.example`，项目模板以根目录 `.env.example` 为准
