"""提供当前尚未开放的工作流恢复契约。"""

from backend.api.schemas import ResumeRequest, ResumeResponse


def no_pending_workflow_response(request: ResumeRequest) -> ResumeResponse:
    """返回当前会话没有待恢复工作流的稳定响应。"""

    message = "当前会话没有待恢复工作流。"
    return ResumeResponse(
        session_id=request.session_id,
        workflow_id=request.workflow_id,
        status="not_found",
        message=message,
        answer=message,
    )
