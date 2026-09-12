"""提供受服务令牌保护的客服对话与工作流恢复接口。"""

import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from agent.xiaozhe import xiaozhe_agent
from agent.xiaozhe.models import ChatRequest, ChatResponse, ResumeRequest, ResumeResponse
from common import ECOMMERCE_SERVICE_TOKEN
from config import config_manager


chat_router = APIRouter(prefix="/chat", tags=["chat"])


def require_service_token(
    x_agent_service_token: Annotated[str | None, Header()] = None,
) -> None:
    """校验电商后端传入的共享服务令牌。"""

    expected = config_manager.get(ECOMMERCE_SERVICE_TOKEN)
    if not expected:
        raise HTTPException(status_code=503, detail="Agent 服务鉴权未配置")
    # 使用恒定时间比较，降低令牌比较过程泄露时序信息的风险。
    if not x_agent_service_token or not hmac.compare_digest(x_agent_service_token, expected):
        raise HTTPException(status_code=401, detail="Agent 服务身份校验失败")


@chat_router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    _: Annotated[None, Depends(require_service_token)],
):
    """接收电商后端请求并执行一轮客服对话。"""

    return await xiaozhe_agent.chat(request)


@chat_router.post("/resume", response_model=ResumeResponse)
async def resume(
    request: ResumeRequest,
    _: Annotated[None, Depends(require_service_token)],
):
    """接收工作流恢复请求并返回当前处理结果。"""

    return await xiaozhe_agent.resume(request)
