"""组装并启动小哲电商 Agent FastAPI 应用。"""

import asyncio
import selectors
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.agents import xiaozhe_agent
from backend.api.routes import router
from backend.config.settings import SERVER_HOST, SERVER_PORT, config_manager
from backend.observability import logger


@asynccontextmanager
async def lifespan(_: FastAPI):
    """在应用关闭时释放 Agent 持有的外部资源。"""

    # yield 之前完成启动，yield 之后统一执行应用级资源清理。
    yield
    await xiaozhe_agent.close()


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用。"""

    app = FastAPI(
        title="Xiaozhe Ecommerce Agent",
        description="小哲电商专属智能客服",
        lifespan=lifespan,
    )

    @app.exception_handler(Exception)
    async def system_exception_handler(_: Request, exc: Exception):
        """记录未捕获异常，并向调用方隐藏服务端内部细节。"""

        logger.exception("未处理的服务异常", exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "服务内部错误"})

    app.include_router(router)
    return app


app = create_app()


async def start_web() -> None:
    """根据配置启动 Uvicorn 服务。"""

    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=config_manager.get(SERVER_HOST),
            port=int(config_manager.get(SERVER_PORT)),
            log_level="info",
            access_log=False,
        )
    )
    await server.serve()


if __name__ == "__main__":
    loop = asyncio.SelectorEventLoop(selector=selectors.SelectSelector())
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_web())
