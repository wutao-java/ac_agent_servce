from langchain.tools import ToolRuntime, tool

from agent.tianji.tools.result import PrePlaceOrder
from config import logger
from util import HttpClientUtil, JsonUtil


@tool
def pre_place_order(course_ids: list[str], runtime: ToolRuntime):
    """根据课程 ID 列表执行预下单。"""
    course_ids = [str(course_id) for course_id in course_ids]
    user_token = runtime.context.user_token
    request_id = runtime.context.request_id
    url = "http://127.0.0.1:10010/ts/orders/prePlaceOrder"

    response_data = HttpClientUtil.get(
        url,
        user_token,
        params={"courseIds": ",".join(course_ids)},
    ) or {}
    data = response_data.get("data")
    if not data:
        logger.error("预下单失败，url=%s, courseIds=%s", url, course_ids)
        return None

    logger.debug(
        "【Tool】pre_place_order url=%s, data=%s, request_id=%s",
        url,
        data,
        request_id,
    )
    return JsonUtil.to_str(PrePlaceOrder.of(data))
