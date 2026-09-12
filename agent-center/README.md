# Agent Center

基于 FastAPI 和 LangGraph 的 Agent 服务。当前实现面向天机课程业务，尚未实现小哲电商客服协议。

## 技术栈

- Python `3.13.5`
- FastAPI + Uvicorn
- LangChain + LangGraph
- MySQL、Redis、PostgreSQL Checkpointer
- Nacos 服务发现

依赖版本以 `environment.yml` 为准。

## 配置

服务启动时会读取当前目录的 `application.yml`，并自动加载仓库根目录的 `.env`。以下环境变量需要按实际环境配置：

| 环境变量 | 用途 |
| --- | --- |
| `AGENT_CENTER_DB_URL` | Agent Center MySQL SQLAlchemy URL |
| `AGENT_CENTER_REDIS_HOST`、`AGENT_CENTER_REDIS_PORT`、`AGENT_CENTER_REDIS_PASSWORD` | Redis 连接配置 |
| `AGENT_CENTER_JWT_PRIVATE_KEY`、`AGENT_CENTER_JWT_PUBLIC_KEY` | JWT Base64 密钥 |
| `AGENT_CENTER_AI_API_KEY` | 模型服务 API Key |
| `AGENT_CENTER_POSTGRES_URL` | LangGraph Checkpointer PostgreSQL URL |
| `AGENT_CENTER_NACOS_*` | Nacos 地址、认证和服务注册 IP |

`application.yml` 当前配置的服务端口为 `18089`。启动前确认 `server.host` 是本机可绑定的地址。

## 创建环境

```powershell
conda env create -f environment.yml
conda activate ac_env_3135
```

## 启动

启动前确保 MySQL、Redis、PostgreSQL 和 Nacos 可访问，并已填写仓库根目录 `.env`。

```powershell
Set-Location agent-center
conda run -n ac_env_3135 python main.py
```

## 当前接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/auth/token` | 使用应用凭据获取 JWT |
| `POST` | `/chat` | 发起 SSE 流式 Agent 对话 |
| `POST` | `/chat/stop` | 停止指定会话 |
| `POST` | `/session` | 创建会话 |
| `GET` | `/session/hot` | 查询指定 Agent 的热门示例 |
| `GET` | `/session/history` | 查询历史会话 |
| `PUT` | `/session/history` | 更新会话标题 |
| `DELETE` | `/session/history` | 删除会话 |
| `GET` | `/session/{agent_id}/{user_id}/{session_id}` | 查询指定会话详情 |

FastAPI 自动文档默认位于 `/docs`。

## 测试

现有测试使用标准库 `unittest`。当测试环境没有运行 Nacos 时，可临时关闭 Nacos 认证，避免客户端在模块导入阶段请求认证接口：

```powershell
$env:AGENT_CENTER_NACOS_USERNAME = ""
$env:AGENT_CENTER_NACOS_PASSWORD = ""
conda run -n ac_env_3135 python -m unittest discover -s tests -v
```

当前基线为 21 个测试通过。

## 小哲电商适配状态

不要将当前 `/chat` 直接配置给电商后端：当前接口接收 `question/sessionId/userToken/agentId` 并返回 SSE，而电商后端期望客服上下文请求和普通 JSON 响应。后续应新增独立的小哲 Agent 协议，避免破坏已有天机课程调用方。
