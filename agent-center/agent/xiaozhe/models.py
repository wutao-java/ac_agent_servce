"""定义小哲电商 Agent 对外接口的请求与响应模型。"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """电商后端发起客服对话时提交的可信请求数据。"""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1)
    runtime_user_id: str = Field(min_length=1)
    runtime_nickname: str | None = None
    runtime_member_level: str | None = None
    runtime_risk_level: str | None = None
    user_message: str = Field(min_length=1)
    agent_mode: str = "production_react"
    reasoning_view: str = "off"
    debug: bool = False
    runtime_context: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """客服对话接口返回的回答与会话状态。"""

    session_id: str
    answer: str
    reasoning_summary: list[str] = Field(default_factory=list)
    session_state: dict[str, Any]


class ResumeRequest(BaseModel):
    """恢复已暂停工作流时提交的审核信息。"""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1)
    workflow_id: str = Field(min_length=1)
    resume_token: str = Field(min_length=1)
    decision: str = Field(min_length=1)
    reviewer_note: str | None = None


class ResumeResponse(BaseModel):
    """工作流恢复接口返回的处理状态与结果。"""

    session_id: str
    workflow_id: str
    status: Literal[
        "approval_resumed",
        "approval_rejected",
        "approval_needs_more_info",
        "invalid_resume_token",
        "not_found",
        "not_paused",
        "resume_failed",
    ]
    message: str
    answer: str | None = None
    workflow: dict[str, Any] | None = None
    session_state: dict[str, Any] | None = None
