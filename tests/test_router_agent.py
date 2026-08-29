from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from langgraph.graph.state import CompiledStateGraph

from agent.BaseAgent import STOP_EVENT, format_sse_data, make_sse_event
from agent.tianji.RouterAgent import RouterAgent


class RouterAgentTest(unittest.TestCase):

    def test_init_graph_compiles_and_writes_mermaid_image(self):
        agent = RouterAgent()
        graph_view = Mock()
        graph_view.draw_mermaid_png.return_value = b"image-bytes"

        with TemporaryDirectory() as temp_dir:
            graph_png_dir = Path(temp_dir) / "graph_png"
            with (
                patch.object(RouterAgent, "GRAPH_PNG_DIR", graph_png_dir),
                patch.object(CompiledStateGraph, "get_graph", return_value=graph_view),
            ):
                agent.init_graph()

            self.assertIsInstance(agent.graph, CompiledStateGraph)
            self.assertEqual(
                (graph_png_dir / "router.jpg").read_bytes(),
                b"image-bytes",
            )


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


if __name__ == "__main__":
    unittest.main()
