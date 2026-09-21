import unittest
import json
from unittest.mock import AsyncMock, Mock

from langgraph.checkpoint.base import get_checkpoint_metadata
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agent.BaseAgent import STOP_EVENT, format_sse_data, make_sse_event
from agent.tianji.RouterAgent import RouterAgent
from agent.tianji.node.BaseNodeAgent import ToolContext
from util import JsonUtil


class RouterAgentTest(unittest.TestCase):

    def test_init_graph_compiles(self):
        agent = RouterAgent()
        agent.init_graph()

        self.assertIsInstance(agent.graph, CompiledStateGraph)

    def test_normalize_intent_strips_and_validates_model_output(self):
        self.assertEqual(RouterAgent._normalize_intent(" knowledge\n"), "KNOWLEDGE")
        self.assertEqual(RouterAgent._normalize_intent("unexpected"), "UNKNOWN")


class RouterAgentExecuteTest(unittest.IsolatedAsyncioTestCase):

    async def test_execute_returns_original_error_and_stop_event(self):
        agent = RouterAgent()
        agent.graph = Mock()
        agent.graph.astream.side_effect = RuntimeError("graph failed")
        agent.reset_stop = Mock()

        with unittest.mock.patch(
            "agent.tianji.RouterAgent.chat_session_dao.update_title"
        ):
            events = [
                event
                async for event in agent.execute(
                    question="课程推荐",
                    session_id="11",
                    user_token="test-token",
                )
            ]

        self.assertEqual(
            events,
            [
                make_sse_event(2001, "graph failed"),
                format_sse_data(STOP_EVENT),
            ],
        )

    async def test_execute_passes_token_in_transient_context(self):
        class EmptyStream:
            def __aiter__(self):
                return self

            async def __anext__(self):
                raise StopAsyncIteration

        agent = RouterAgent()
        agent.graph = Mock()
        agent.graph.astream.return_value = EmptyStream()
        agent.reset_stop = Mock()

        with unittest.mock.patch(
            "agent.tianji.RouterAgent.chat_session_dao.update_title"
        ):
            events = [
                event
                async for event in agent.execute(
                    question="课程推荐",
                    session_id="11",
                    user_token="test-token",
                )
            ]

        config = agent.graph.astream.call_args.kwargs["config"]
        configurable = config["configurable"]

        self.assertEqual(events, [format_sse_data(STOP_EVENT)])
        self.assertEqual(configurable["thread_id"], "11")
        self.assertNotIn("user_token", configurable)
        self.assertNotIn("request_id", configurable)
        self.assertIsInstance(configurable["tool_context"], ToolContext)
        self.assertEqual(configurable["tool_context"].user_token, "test-token")

        checkpoint_metadata = get_checkpoint_metadata(
            config,
            {"source": "input", "step": -1, "parents": {}},
        )
        self.assertNotIn("test-token", repr(checkpoint_metadata))
        self.assertNotIn(configurable["tool_context"].request_id, repr(checkpoint_metadata))

    async def test_execute_emits_course_and_order_cards_before_stop_event(self):
        class MessageStream:
            def __init__(self, events):
                self.events = iter(events)
                self.closed = False

            def __aiter__(self):
                return self

            async def __anext__(self):
                try:
                    return next(self.events)
                except StopIteration as exc:
                    raise StopAsyncIteration from exc

            async def aclose(self):
                self.closed = True

        stream = MessageStream([
            (
                (),
                (
                    ToolMessage(
                        content=JsonUtil.to_str({
                            "id": "course-1",
                            "name": "Java课程",
                            "price": 199.0,
                            "validDuration": 999,
                            "usePeople": "Java开发者",
                            "detail": "课程详情",
                        }),
                        tool_call_id="course-call",
                        name="query_course_by_id",
                    ),
                    {"tags": []},
                ),
            ),
            (
                (),
                (
                    ToolMessage(
                        content=JsonUtil.to_str({
                            "count": 1,
                            "totalAmount": 199.0,
                            "discountAmount": 6.0,
                            "couponName": "优惠6元",
                            "payAmount": 193.0,
                            "courseIds": ["course-1"],
                            "orderId": "order-1",
                            "couponId": "coupon-1",
                        }),
                        tool_call_id="order-call",
                        name="pre_place_order",
                    ),
                    {"tags": []},
                ),
            ),
            ((), (AIMessage(content="已为你准备好课程。"), {"tags": []})),
        ])
        agent = RouterAgent()
        agent.graph = Mock()
        agent.graph.astream.return_value = stream
        agent.reset_stop = Mock()
        agent.is_stop = Mock(return_value=False)

        with unittest.mock.patch(
            "agent.tianji.RouterAgent.chat_session_dao.update_title"
        ) as update_title:
            events = [
                event
                async for event in agent.execute(
                    question="我要购买课程",
                    session_id="session-1",
                    user_token="test-token",
                )
            ]

        payloads = [
            json.loads(event.removeprefix("data: ").strip())
            for event in events
        ]
        self.assertEqual(payloads[0]["eventType"], 1001)
        self.assertEqual(payloads[1]["eventType"], 1003)
        self.assertEqual(
            payloads[1]["eventData"]["courseInfo_course-1"]["name"],
            "Java课程",
        )
        self.assertEqual(
            payloads[1]["eventData"]["prePlaceOrder"]["payAmount"],
            193.0,
        )
        self.assertEqual(payloads[2], STOP_EVENT)
        agent.reset_stop.assert_called_once_with("session-1")
        update_title.assert_called_once_with("session-1", 1001, "我要购买课程")

    async def test_execute_closes_stream_when_stop_flag_exists(self):
        class MessageStream:
            def __init__(self):
                self.closed = False
                self.sent = False

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.sent:
                    raise StopAsyncIteration
                self.sent = True
                return (), (AIMessage(content="不应输出"), {"tags": []})

            async def aclose(self):
                self.closed = True

        stream = MessageStream()
        agent = RouterAgent()
        agent.graph = Mock()
        agent.graph.astream.return_value = stream
        agent.reset_stop = Mock()
        agent.is_stop = Mock(return_value=True)

        with unittest.mock.patch(
            "agent.tianji.RouterAgent.chat_session_dao.update_title"
        ):
            events = [
                event
                async for event in agent.execute(
                    question="停止测试",
                    session_id="session-1",
                    user_token="test-token",
                )
            ]

        self.assertEqual(events, [format_sse_data(STOP_EVENT)])
        self.assertTrue(stream.closed)

    async def test_execute_skips_tool_result_after_stop(self):
        class MessageStream:
            def __init__(self):
                self.events = iter([
                    (
                        (),
                        (
                            ToolMessage(
                                content=JsonUtil.to_str({
                                    "id": "course-1",
                                    "name": "Java课程",
                                    "price": 199.0,
                                    "validDuration": 999,
                                    "usePeople": "Java开发者",
                                    "detail": "课程详情",
                                }),
                                tool_call_id="course-call",
                                name="query_course_by_id",
                            ),
                            {"tags": []},
                        ),
                    ),
                    ((), (AIMessage(content="不应输出"), {"tags": []})),
                ])
                self.closed = False

            def __aiter__(self):
                return self

            async def __anext__(self):
                try:
                    return next(self.events)
                except StopIteration as exc:
                    raise StopAsyncIteration from exc

            async def aclose(self):
                self.closed = True

        stream = MessageStream()
        agent = RouterAgent()
        agent.graph = Mock()
        agent.graph.astream.return_value = stream
        agent.reset_stop = Mock()
        agent.is_stop = Mock(side_effect=[False, True])

        with unittest.mock.patch(
            "agent.tianji.RouterAgent.chat_session_dao.update_title"
        ):
            events = [
                event
                async for event in agent.execute(
                    question="停止测试",
                    session_id="session-1",
                    user_token="test-token",
                )
            ]

        self.assertEqual(events, [format_sse_data(STOP_EVENT)])
        self.assertTrue(stream.closed)


class RouterAgentSessionTest(unittest.IsolatedAsyncioTestCase):

    async def test_delete_session_deletes_checkpoints(self):
        agent = RouterAgent()
        agent.checkpointer = Mock()
        agent.checkpointer.adelete_thread = AsyncMock()

        await agent.delete_session("session-1")

        agent.checkpointer.adelete_thread.assert_awaited_once_with("session-1")

    async def test_session_detail_restores_tool_params_on_assistant_message(self):
        agent = RouterAgent()
        agent.graph = Mock()
        agent.graph.aget_state = AsyncMock(return_value=Mock(values={
            "messages": [
                HumanMessage(content="介绍课程"),
                ToolMessage(
                    content=JsonUtil.to_str({
                        "id": "course-1",
                        "name": "Java课程",
                        "price": 199.0,
                        "validDuration": 999,
                        "usePeople": "Java开发者",
                        "detail": "课程详情",
                    }),
                    tool_call_id="course-call",
                    name="query_course_by_id",
                ),
                AIMessage(content="这门课程适合你。"),
            ],
        }))

        result = await agent.session_detail(1, "session-1")

        self.assertEqual(result[0]["type"], "USER")
        self.assertEqual(result[1]["type"], "ASSISTANT")
        self.assertEqual(
            result[1]["params"]["courseInfo_course-1"].name,
            "Java课程",
        )


if __name__ == "__main__":
    unittest.main()
