import hmac

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse, PlainTextResponse
from web.router import auth_router, session_router,chat_router
from agent.Agents import AGENTS
from agent.prompts import system_prompt_config
from config import close_async_pg_pool,nacos_config,config_manager,logger
from common import *


# ========================= 创建 FastAPI 实例 =========================
app = FastAPI(
    title="Agent Center Web Server",
    description="黑马程序员智能体中心"
)


# ========================= 异常处理 =========================
def system_exception_handler(req: Request, exc: Exception):
    """
    全局异常处理函数，将异常转换为 500 响应
    """
    return PlainTextResponse(
        content=str(exc),
        status_code=500
    )


# 添加全局异常处理器
app.add_exception_handler(Exception, system_exception_handler)


# ========================= 网关来源校验 =========================
def _to_bool(value, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() not in {"false", "0", "no", "off"}


def _is_excluded_path(path: str, exclude_paths: list[str]) -> bool:
    for exclude_path in exclude_paths:
        normalized = exclude_path.rstrip("/")
        if path == normalized or path.startswith(normalized + "/"):
            return True
    return False


@app.middleware("http")
async def gateway_auth_middleware(request: Request, call_next):
    enabled = _to_bool(config_manager.get(GATEWAY_AUTH_ENABLED, True))
    exclude_paths = config_manager.get(GATEWAY_AUTH_EXCLUDE_PATHS, []) or []
    if not enabled or _is_excluded_path(request.url.path, exclude_paths):
        return await call_next(request)

    header_name = config_manager.get(GATEWAY_AUTH_HEADER, "X-Gateway-Token")
    secret = config_manager.get(GATEWAY_AUTH_SECRET)
    if not secret:
        logger.error("网关来源校验密钥未配置: %s", GATEWAY_AUTH_SECRET)
        return JSONResponse(
            status_code=503,
            content={"detail": "Gateway auth secret is not configured"},
        )

    request_token = request.headers.get(header_name, "")
    if not hmac.compare_digest(request_token, secret):
        logger.warning("拒绝非网关来源请求: path=%s", request.url.path)
        return JSONResponse(
            status_code=403,
            content={"detail": "Forbidden"},
        )

    return await call_next(request)

# ========================= Nacos 注册与注销 =========================
def register_service():
    """
    注册智能体中心服务到 Nacos 服务发现
    """
    client = nacos_config.get_discovery_client()  # 获取 Nacos 注册客户端
    ip = nacos_config.get_discovery_ip()  # 服务 IP
    service_name = nacos_config.get_discovery_name()  # 服务名称
    port = int(config_manager.get(SERVER_PORT))  # 服务端口
    group_name = nacos_config.get_discovery_group()  # 分组名称

    # 将实例注册到 Nacos
    result = client.add_naming_instance(
        service_name=service_name,
        ip=ip,
        port=port,
        group_name=group_name,
        heartbeat_interval=10  # 心跳间隔 10 秒
    )
    logger.info(f"✅ Registered {service_name} to Nacos: {result}")
    return result

def deregister_service():
    """
    注销智能体中心服务
    """
    ip = nacos_config.get_discovery_ip()
    service_name = nacos_config.get_discovery_name()
    port = int(config_manager.get(SERVER_PORT))

    # 从 Nacos 注销实例
    result = nacos_config.get_discovery_client().remove_naming_instance(
        service_name, ip, port
    )
    logger.info(f"🧹 Deregistered {service_name} from Nacos")


# ========================= 启动事件 =========================
async def startup():
    """
    启动 web 服务时执行：
    - 初始化所有 Agent
    """
    # 初始化pg数据库连接池
    await close_async_pg_pool()
    # 初始化系统提示词配置与热更新线程
    system_prompt_config.start()
    # 初始化所有 Agent
    for agent in AGENTS.values():
        await agent.init()
    # nacos服务注册
    register_service()

# ========================= 关闭事件 =========================
async def shutdown():
    """
    停止 web 服务时执行：
    - 销毁所有 Agent
    """
    # 断开pg数据库连接池
    await close_async_pg_pool()
    # 销毁所有 Agent
    for agent in AGENTS.values():
        await agent.destroy()
    # nacos服务销毁
    deregister_service()


# ========================= 事件注册 =========================
# 启动事件：初始化数据库、Agents、注册服务
app.add_event_handler("startup", startup)
# 关闭事件：关闭资源、注销服务
app.add_event_handler("shutdown", shutdown)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(session_router, prefix="/session", tags=["session"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
