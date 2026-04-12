# infra 目录说明

`infra/` 是项目级工程基础设施目录，用于统一管理本地运行、联调和演示方式。
它不属于 `app/` 七层业务分层，不承载业务代码。

当前目录提供：
- `Dockerfile`：构建 app 运行镜像
- `compose.yaml`：编排 app + redis + qdrant
- 根目录 `.env.example`：当前阶段唯一配置文件（单一事实来源）

## 1. 前置条件

1. 已安装 Docker Desktop（或等价 Docker + Compose 环境）
2. 当前路径位于仓库根目录 `vi_ai_core_service`

## 2. 启动步骤

1. 在仓库根目录按需编辑 `.env.example`（当前直接作为运行配置）：
```powershell
# 当前阶段直接使用根目录 .env.example，不再复制 .env
```

2. 启动 app + redis + qdrant：
```powershell
docker compose -f infra/compose.yaml up -d --build
```

3. 查看服务状态：
```powershell
docker compose -f infra/compose.yaml ps
```

### 2.1 本地目录热挂载（已默认启用）

当前 `infra/compose.yaml` 已为 `app` 服务默认启用：

- 目录挂载：`../app:/workspace/app`
- 依赖同步：`../requirements.txt:/workspace/requirements.txt:ro`
- 启动参数：`pip install -r /workspace/requirements.txt && uvicorn ... --reload`
- 监听兼容：`WATCHFILES_FORCE_POLLING=true`

这意味着你在本地修改 `app/` 下 Python 代码后，容器内服务会自动重载，不需要每次重建镜像。
也意味着你在本地修改 `requirements.txt` 后，重启 `app` 容器时会自动安装最新依赖（例如 `python-multipart`）。

说明：如果你修改了 `infra/Dockerfile` 或系统层依赖，仍需执行 `up --build` 重新构建镜像。

### 2.2 internal_console 独立编排说明

`internal_console` 已迁移为独立 docker 编排，不再由本目录 `compose.yaml` 管理。  
请使用 `internal_console/infra/compose.yaml` 独立启动前端控制台。

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

查看 qdrant 日志：
```powershell
docker compose -f infra/compose.yaml logs -f qdrant
```

## 5. 停止与清理

停止服务：
```powershell
docker compose -f infra/compose.yaml down
```

停止并删除镜像与卷（可选）：
```powershell
docker compose -f infra/compose.yaml down --rmi local --volumes
```

## 6. 角色说明

- `app`：运行 FastAPI HTTP 服务（入口：`app.server:app`）
- `redis`：提供短期记忆持久化依赖
- `qdrant`：提供 Phase 6 知识向量索引依赖

其中 `infra/compose.yaml` 通过 `env_file: ../.env.example` 读取根目录 `.env.example`。
`CONTEXT_REDIS_URL=redis://redis:6379/0` 使用 compose 服务名 `redis` 进行容器内网络访问。
`RAG_QDRANT_URL=http://qdrant:6333` 使用 compose 服务名 `qdrant` 进行容器内网络访问。

## 7. 运行边界

1. 当前方案仅用于本地开发、联调、演示
2. 不代表生产部署方案
3. 不包含 Kubernetes、Helm、生产高可用 Redis 编排
4. `infra/` 不再维护独立项目级 `.env.example`，配置以根目录 `.env.example` 为准
5. 当前阶段不处理 API key 安全治理，安全治理将在后续独立阶段处理
6. 热挂载仅覆盖 `app/` 目录代码，依赖和镜像层改动不在热重载范围内
