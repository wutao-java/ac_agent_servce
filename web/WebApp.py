from fastapi import FastAPI, Request
from starlette.responses import PlainTextResponse
from web.router import auth_router, session_router,chat_router
from agent.Agents import AGENTS
from config import get_async_pg_pool, close_async_pg_pool

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


# ========================= 启动事件 =========================
async def startup():
    """
    启动 web 服务时执行：
    - 初始化所有 Agent
    """

    await close_async_pg_pool()

    # 初始化所有 Agent
    for agent in AGENTS.values():
        await agent.init()


# ========================= 关闭事件 =========================
async def shutdown():
    """
    停止 web 服务时执行：
    - 销毁所有 Agent
    """
    await close_async_pg_pool()

    # 销毁所有 Agent
    for agent in AGENTS.values():
        await agent.destroy()


# ========================= 事件注册 =========================
# 启动事件：初始化数据库、Agents、注册服务
app.add_event_handler("startup", startup)
# 关闭事件：关闭资源、注销服务
app.add_event_handler("shutdown", shutdown)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(session_router, prefix="/session", tags=["session"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])