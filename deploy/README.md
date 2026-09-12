# Deployment

`docker-compose.yml` 用于本地启动小哲电商，不包含 Agent Center。

## 服务

| Compose 服务 | 容器端口 | 默认宿主机端口 |
| --- | --- | --- |
| `mysql` | `3306` | `3306` |
| `ecommerce-backend` | `8081` | `8081` |
| `ecommerce-frontend` | `80` | `5174` |

MySQL 数据保存在 Compose 命名卷 `mysql-data` 中。

## 配置

从仓库根目录准备 `.env`。以下变量是启动必填项：

- `MYSQL_ROOT_PASSWORD`
- `AGENT_SERVICE_AUTH_TOKEN`

其他变量均在 `.env.example` 中提供本地默认值或示例。

## 启动与检查

```powershell
docker compose --env-file .env -f deploy/docker-compose.yml up --build -d
docker compose --env-file .env -f deploy/docker-compose.yml ps
docker compose --env-file .env -f deploy/docker-compose.yml logs -f ecommerce-backend
```

健康检查：

```powershell
Invoke-RestMethod http://localhost:8081/actuator/health
```

## 停止

```powershell
docker compose --env-file .env -f deploy/docker-compose.yml down
```

`down` 不会删除 MySQL 数据卷。只有明确需要清空本地电商数据时才使用 `down -v`。

## Agent 连接

当 Agent 运行在 Windows 宿主机时，容器内默认通过 `http://host.docker.internal:8000` 访问。若未来将 Agent 加入同一个 Compose 网络，应把 `AGENT_SERVICE_BASE_URL` 改为对应 Compose 服务名。

生产部署时应移除 MySQL 宿主机端口映射、使用密钥管理服务注入凭据，并在电商前端之前配置 TLS 入口。
