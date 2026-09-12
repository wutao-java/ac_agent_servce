"""创建 FastAPI 应用并注册生命周期、系统接口和业务路由。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from agent import xiaozhe_agent
from config import logger
from web.router import chat_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    """在应用关闭时释放 Agent 持有的外部资源。"""

    yield
    await xiaozhe_agent.close()


app = FastAPI(
    title="Xiaozhe Ecommerce Agent",
    description="小哲电商专属智能客服",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def system_exception_handler(_: Request, exc: Exception):
    """记录未处理异常并返回统一的服务端错误响应。"""

    logger.exception("未处理的服务异常", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "服务内部错误"})


@app.get("/health", tags=["system"])
async def health():
    """返回不依赖外部服务的进程健康状态。"""

    return {"status": "ok"}


@app.get("/capabilities", tags=["system"])
async def capabilities():
    """声明当前 Agent 已开放及尚未开放的能力。"""

    return {
        "schema_version": "agent_capabilities_v1",
        "agent": {"name": "xiaozhe-ecommerce-agent", "version": "1.0.0"},
        "endpoints": {
            "health": True,
            "chat": True,
            "chat_resume": True,
            "trace": False,
            "eval_run": False,
        },
        "features": {
            "chat": True,
            "tool_calling": True,
            "realtime_business_facts": True,
            "runtime_context": True,
            "checkpoint": True,
            "human_approval": False,
        },
        "disabled_reasons": {
            "human_approval": "高风险写操作工作流尚未启用",
            "trace": "当前版本未开放运行轨迹接口",
            "eval_run": "当前版本未开放在线评测接口",
        },
    }


app.include_router(chat_router)
