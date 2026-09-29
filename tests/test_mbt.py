"""Model-based TCP RPC tests for practical assignment variant 26."""

import sys
import threading
from pathlib import Path

from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, rule

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from model import DataModel
from rpc import RPCClient, RPCServer


class RPCStateMachine(RuleBasedStateMachine):
    """Test all 13 RPC methods through a real TCP connection."""

    def __init__(self) -> None:
        super().__init__()

        self.server = RPCServer(
            ("127.0.0.1", 0),
            DataModel(),
        )

        self.port = self.server.server_address[1]

        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )
        self.thread.start()

        self.client = RPCClient(
            host="127.0.0.1",
            port=self.port,
        )

        self.case_number = 0

    def teardown(self) -> None:
        """Stop the TCP server after each generated state machine."""
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    @initialize()
    def initial_state(self) -> None:
        """Check that the server starts with empty tables."""
        assert self.client.get_profiles() == []
        assert self.client.get_queries() == []
        assert self.client.get_feedback() == []

        result = self.client.recent_feedback_projection(now=1000)
        assert result == []

    @rule(value=st.integers(min_value=1, max_value=10_000))
    def complete_rpc_flow(self, value: int) -> None:
        """Exercise all CRUD-style RPC operations in one generated flow."""
        self.case_number += 1

        base = self.case_number * 10_000
        profile_key = base + 1
        query_key = base + 2
        feedback_key = base + 3

        profile = self.client.create_profile(
            key=profile_key,
            created=995,
            ip="127.0.0.1",
            locale="ru_RU",
            platform="windows",
            user_agent=f"hypothesis-{value}",
        )

        assert profile["key"] == profile_key

        profiles = self.client.get_profiles()
        assert any(
            item["key"] == profile_key
            for item in profiles
        )

        fetched_profile = self.client.get_profile(profile_key)
        assert fetched_profile["key"] == profile_key

        edited_profile = self.client.edit_profile(
            profile_key,
            locale="en_US",
        )
        assert edited_profile["locale"] == "en_US"

        query = self.client.create_query(
            key=query_key,
            created=995,
            parameter=f"parameter-{value}",
            profile=profile_key,
            description="generated query",
            tags=f"tag-{value}",
            status="new",
        )

        assert query["key"] == query_key

        queries = self.client.get_queries()
        assert any(
            item["key"] == query_key
            for item in queries
        )

        fetched_query = self.client.get_query(query_key)
        assert fetched_query["key"] == query_key

        edited_query = self.client.edit_query(
            query_key,
            status="done",
            tags=f"tag-edited-{value}",
        )

        assert edited_query["status"] == "done"

        feedback = self.client.create_feedback(
            key=feedback_key,
            created=996,
            response=f"response-{value}",
            status="success",
            exception="",
            query=query_key,
            cache_hit=0,
        )

        assert feedback["key"] == feedback_key

        all_feedback = self.client.get_feedback()
        assert any(
            item["key"] == feedback_key
            for item in all_feedback
        )

        fetched_feedback = self.client.get_feedback_item(
            feedback_key
        )
        assert fetched_feedback["key"] == feedback_key

        edited_feedback = self.client.edit_feedback(
            feedback_key,
            cache_hit=1,
        )
        assert edited_feedback["cache_hit"] == 1

        projection = self.client.recent_feedback_projection(
            now=1000
        )

        expected = {
            "cache_hit": 1,
            "exception": "",
            "tags": f"tag-edited-{value}",
        }

        assert expected in projection


TestRPCStateMachine = RPCStateMachine.TestCase

TestRPCStateMachine.settings = settings(
    max_examples=10,
    stateful_step_count=3,
    deadline=None,
)