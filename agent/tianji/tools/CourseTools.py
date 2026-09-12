from langchain.tools import ToolRuntime, tool

from agent.tianji.tools.result import CourseInfo
from config import logger
from util import HttpClientUtil, JsonUtil


@tool
def query_course_by_id(course_id: str, runtime: ToolRuntime):
    """根据课程 ID 查询课程信息。"""
    user_token = runtime.context.user_token
    request_id = runtime.context.request_id
    url = f"http://127.0.0.1:10010/cs/courses/baseInfo/{course_id}"

    response_data = HttpClientUtil.get(url, user_token) or {}
    data = response_data.get("data")
    if not data:
        logger.error("查询课程失败，url=%s", url)
        return None

    logger.debug(
        "【Tool】query_course_by_id url=%s, data=%s, request_id=%s",
        url,
        data,
        request_id,
    )
    return JsonUtil.to_str(CourseInfo.of(data))
