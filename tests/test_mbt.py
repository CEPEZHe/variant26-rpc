"""Model-based TCP RPC tests for practical assignment variant 26."""

import threading

from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, rule

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

    def _profile_flow(self, key: int, value: int) -> None:
        profile = self.client.create_profile(
            key=key,
            created=995,
            ip="127.0.0.1",
            locale="ru_RU",
            platform="windows",
            user_agent=f"hypothesis-{value}",
        )
        assert profile["key"] == key

        profiles = self.client.get_profiles()
        assert any(item["key"] == key for item in profiles)

        fetched = self.client.get_profile(key)
        assert fetched["key"] == key

        edited = self.client.edit_profile(
            key,
            locale="en_US",
        )
        assert edited["locale"] == "en_US"

    def _query_flow(
        self,
        key: int,
        profile_key: int,
        value: int,
    ) -> None:
        query = self.client.create_query(
            key=key,
            created=995,
            parameter=f"parameter-{value}",
            profile=profile_key,
            description="generated query",
            tags=f"tag-{value}",
            status="new",
        )
        assert query["key"] == key

        queries = self.client.get_queries()
        assert any(item["key"] == key for item in queries)

        fetched = self.client.get_query(key)
        assert fetched["key"] == key

        edited = self.client.edit_query(
            key,
            status="done",
            tags=f"tag-edited-{value}",
        )
        assert edited["status"] == "done"

    def _feedback_flow(
        self,
        key: int,
        query_key: int,
        value: int,
    ) -> None:
        feedback = self.client.create_feedback(
            key=key,
            created=996,
            response=f"response-{value}",
            status="success",
            exception="",
            query=query_key,
            cache_hit=0,
        )
        assert feedback["key"] == key

        all_feedback = self.client.get_feedback()
        assert any(item["key"] == key for item in all_feedback)

        fetched = self.client.get_feedback_item(key)
        assert fetched["key"] == key

        edited = self.client.edit_feedback(
            key,
            cache_hit=1,
        )
        assert edited["cache_hit"] == 1

    def _check_projection(self, value: int) -> None:
        projection = self.client.recent_feedback_projection(now=1000)
        expected = {
            "cache_hit": 1,
            "exception": "",
            "tags": f"tag-edited-{value}",
        }
        assert expected in projection

    @rule(value=st.integers(min_value=1, max_value=10_000))
    def complete_rpc_flow(self, value: int) -> None:
        self.case_number += 1
        base = self.case_number * 10_000

        profile_key = base + 1
        query_key = base + 2
        feedback_key = base + 3

        self._profile_flow(profile_key, value)
        self._query_flow(query_key, profile_key, value)
        self._feedback_flow(feedback_key, query_key, value)
        self._check_projection(value)


TestRPCStateMachine = RPCStateMachine.TestCase

TestRPCStateMachine.settings = settings(
    max_examples=10,
    stateful_step_count=3,
    deadline=None,
)
