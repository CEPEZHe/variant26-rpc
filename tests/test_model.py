"""Focused unit tests for the local data model."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from model import DataModel


def test_projection_full_outer_join() -> None:
    model = DataModel()
    model.create_profile(
        key=1,
        created=1000,
        ip="127.0.0.1",
        locale="ru_RU",
        platform="linux",
        user_agent="pytest",
    )
    model.create_query(
        key=10,
        created=1000,
        parameter="p",
        profile=1,
        description="d",
        tags="alpha",
        status="ok",
    )
    model.create_feedback(
        key=20,
        created=1001,
        response="r",
        status="ok",
        exception="",
        query=10,
        cache_hit=1,
    )
    assert model.recent_feedback_projection(now=1100) == [
        {"cache_hit": 1, "exception": "", "tags": "alpha"}
    ]
