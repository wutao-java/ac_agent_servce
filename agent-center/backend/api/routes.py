"""提供 Agent 健康检查、能力声明和客服接口。"""

import hmac
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.agents import xiaozhe_agent
from backend.api.schemas import ChatRequest, ChatResponse, ResumeRequest, ResumeResponse
from backend.config import config_manager, load_agent_capabilities
from backend.config.settings import ECOMMERCE_SERVICE_TOKEN


router = APIRouter()


def require_service_token(
    x_agent_service_token: Annotated[str | None, Header()] = None,
) -> None:
    """校验电商后端传入的共享服务令牌。"""

    expected = config_manager.get(ECOMMERCE_SERVICE_TOKEN)
    if not expected:
        raise HTTPException(status_code=503, detail="Agent 服务鉴权未配置")
    # 使用常量时间比较，避免普通字符串比较泄露令牌匹配进度。
    if not x_agent_service_token or not hmac.compare_digest(x_agent_service_token, expected):
        raise HTTPException(status_code=401, detail="Agent 服务身份校验失败")


@router.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """返回不依赖外部服务的进程健康状态。"""

    return {"status": "ok"}


@router.get("/capabilities", tags=["system"])
async def capabilities() -> dict[str, Any]:
    """返回调试后台使用的 Agent 能力声明。"""

    return load_agent_capabilities()


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    request: ChatRequest,
    _: Annotated[None, Depends(require_service_token)],
) -> ChatResponse:
    """执行一轮客服对话。"""

    return await xiaozhe_agent.chat(request)


@router.post("/chat/resume", response_model=ResumeResponse, tags=["chat"])
async def resume(
    request: ResumeRequest,
    _: Annotated[None, Depends(require_service_token)],
) -> ResumeResponse:
    """恢复已暂停的工作流。"""

    return await xiaozhe_agent.resume(request)
