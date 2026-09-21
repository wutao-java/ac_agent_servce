import unittest
from unittest.mock import Mock, patch

from agent.tianji.node import RecommendAgent
from agent.tianji.node.BaseNodeAgent import ToolContext
from agent.tianji.tools import query_recommend_data
from util import JsonUtil


class RecommendAgentTest(unittest.TestCase):

    def test_registers_recommend_and_course_detail_tools(self):
        tools = RecommendAgent().tools()
        tool_names = [tool.name for tool in tools]

        self.assertEqual(
            tool_names,
            ["query_recommend_data", "query_course_by_id"],
        )
        schema = tools[0].tool_call_schema.model_json_schema()
        self.assertEqual(list(schema["properties"]), ["keyword"])

    @patch("agent.tianji.tools.CourseTools.HttpClientUtil.get")
    def test_query_recommend_data_returns_top_three_course_ids(self, get):
        get.return_value = {"data": [101, 102, 103, 104]}
        runtime = Mock(
            context=ToolContext(
                user_token="test-token",
                request_id="request-1",
            )
        )

        result = query_recommend_data.func("Java", runtime)

        self.assertEqual(JsonUtil.to_obj(result), [101, 102, 103])
        get.assert_called_once_with(
            "http://127.0.0.1:10010/ss/courses/name",
            "test-token",
            params={"keyword": "Java"},
        )

    @patch("agent.tianji.tools.CourseTools.HttpClientUtil.get")
    def test_query_recommend_data_returns_empty_list_when_no_course_matches(self, get):
        get.return_value = {"data": []}
        runtime = Mock(
            context=ToolContext(
                user_token="test-token",
                request_id="request-1",
            )
        )

        result = query_recommend_data.func("不存在的方向", runtime)

        self.assertEqual(JsonUtil.to_obj(result), [])


if __name__ == "__main__":
    unittest.main()
