# Xiaozhe Ecommerce Agent

面向小哲电商的 FastAPI + LangGraph 专属客服 Agent。电商后端负责登录态、用户身份和业务数据归属校验，Agent 仅通过受保护的 HTTP API 查询业务事实，不直接访问电商数据库。

## 当前能力

- 商品、价格、库存和活动查询
- 当前用户订单与物流查询
- 用户偏好、优惠券、FAQ 和售后规则查询
- LangGraph 会话记忆；配置 PostgreSQL 时持久化，否则仅保存在当前进程
- 电商后端与 Agent 双向服务令牌校验

退款、退货、取消订单等写操作和人工确认恢复工作流尚未开放。`/chat/resume` 已提供稳定契约，但在没有待恢复工作流时返回 `not_found`。

## 配置

服务读取 `application.yml`，并加载仓库根目录的 `.env`。

| 环境变量 | 用途 |
| --- | --- |
| `AGENT_CENTER_AI_API_KEY` | 模型服务 API Key |
| `AGENT_SERVICE_AUTH_TOKEN` | 电商后端与 Agent 双向调用的共享服务令牌 |
| `ECOMMERCE_BACKEND_BASE_URL` | 电商后端地址，默认 `http://127.0.0.1:8081` |
| `AGENT_CENTER_POSTGRES_URL` | 可选的 LangGraph Checkpointer PostgreSQL URL |

禁止把真实令牌和 API Key 提交到仓库。

## 启动

```powershell
conda env create -f environment.yml
conda activate ac_env_3135
Set-Location agent-center
python -m backend.main
```

服务默认监听 `127.0.0.1:8000`。

## 目录结构

当前服务沿用课程后端的分层方式，并在对应目录中保留商城集成、工具调用和会话状态能力：

```text
backend/
  api/             # HTTP 路由和请求响应模型
  agents/          # 客服 Agent 编排
  config/          # 应用配置
  integrations/    # 电商后端客户端
  models/          # 大模型客户端
  observability/   # 日志与运行观测
  state/           # LangGraph Checkpointer
  tools/           # 只读业务工具和运行时上下文
  workflows/       # 工作流恢复契约
  main.py          # FastAPI 应用入口
```

## 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/health` | 进程健康检查 |
| `GET` | `/capabilities` | 当前 Agent 能力声明 |
| `POST` | `/chat` | 电商客服对话，返回普通 JSON |
| `POST` | `/chat/resume` | 工作流恢复契约；当前未启用写操作 |

`POST /chat` 和 `POST /chat/resume` 必须携带 `X-Agent-Service-Token`。电商后端调用 Agent 时会自动发送该请求头。

## 测试

测试不需要运行 MySQL、Redis、Nacos 或 PostgreSQL：

```powershell
conda run -n ac_env_3135 python -m unittest discover -s tests -v
```

Nacos 注册代码暂时隔离在 `backend/config/nacos.py`，不会在启动时加载，待网关接入方案确定后再启用或替换。
