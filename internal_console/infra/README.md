# internal_console/infra 目录说明

`internal_console/infra/` 用于管理内部控制台前端的 Docker 构建与编排。
该目录与后端 `infra/` 独立，避免 service 与 internal_console 混编排。

当前目录提供：
- `Dockerfile`：构建 internal_console 镜像
- `compose.yaml`：编排 internal_console 单服务

## 1. 启动

在仓库根目录执行：

```powershell
docker compose -f internal_console/infra/compose.yaml up -d --build
```

## 2. 查看状态与日志

```powershell
docker compose -f internal_console/infra/compose.yaml ps
docker compose -f internal_console/infra/compose.yaml logs -f internal_console
```

## 3. 重启与自动重打包

当前 `internal_console` 服务启动脚本为：

- `/app/infra/start.sh`

脚本行为：

1. 比较 `package-lock.json` 的哈希与 `node_modules` 内记录
2. 仅在“首次启动”或“lockfile 变化”时执行 `npm ci`
3. 每次启动都执行 `npm run build` 并 `npm run preview`

因此在 Docker Desktop 对 `vi_ai_core_internal_console` 执行 `Restart` 时：

- 不会每次都重新下载依赖包
- 仍会自动重新构建并启动最新代码

## 4. 停止与清理

```powershell
docker compose -f internal_console/infra/compose.yaml down
```

```powershell
docker compose -f internal_console/infra/compose.yaml down --rmi local --volumes
```
