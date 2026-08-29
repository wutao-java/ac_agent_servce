import unittest
from unittest.mock import AsyncMock, Mock

from langgraph.checkpoint.base import get_checkpoint_metadata
from langgraph.graph.state import CompiledStateGraph

from agent.BaseAgent import STOP_EVENT, format_sse_data, make_sse_event
from agent.tianji.RouterAgent import RouterAgent
from agent.tianji.node.BaseNodeAgent import ToolContext


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


class RouterAgentSessionTest(unittest.IsolatedAsyncioTestCase):

    async def test_delete_session_deletes_checkpoints(self):
        agent = RouterAgent()
        agent.checkpointer = Mock()
        agent.checkpointer.adelete_thread = AsyncMock()

        await agent.delete_session("session-1")

        agent.checkpointer.adelete_thread.assert_awaited_once_with("session-1")


if __name__ == "__main__":
    unittest.main()
