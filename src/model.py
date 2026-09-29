"""In-memory data access model for practical assignment variant 26."""

from __future__ import annotations

import time
from typing import Any

PROFILE_FIELDS = ["key", "created", "ip", "locale", "platform", "user_agent"]
QUERY_FIELDS = [
    "key",
    "created",
    "parameter",
    "profile",
    "description",
    "tags",
    "status",
]
FEEDBACK_FIELDS = [
    "key",
    "created",
    "response",
    "status",
    "exception",
    "query",
    "cache_hit",
]


class DataModel:
    """Store Profile, Query and Feedback records as lists in memory."""

    def __init__(self) -> None:
        self.profiles: list[list[Any]] = []
        self.queries: list[list[Any]] = []
        self.feedback: list[list[Any]] = []

    @staticmethod
    def _to_dict(record: list[Any], fields: list[str]) -> dict[str, Any]:
        return dict(zip(fields, record, strict=True))

    @staticmethod
    def _find(table: list[list[Any]], key: int) -> list[Any]:
        for record in table:
            if record[0] == key:
                return record
        raise KeyError(f"record with key={key} not found")

    @staticmethod
    def _create(
        table: list[list[Any]], fields: list[str], values: dict[str, Any]
    ) -> dict[str, Any]:
        missing = [field for field in fields if field not in values]
        extra = [field for field in values if field not in fields]
        if missing or extra:
            raise ValueError(f"invalid fields: missing={missing}, extra={extra}")
        if any(record[0] == values["key"] for record in table):
            raise ValueError(f"duplicate key={values['key']}")
        record = [values[field] for field in fields]
        table.append(record)
        return DataModel._to_dict(record, fields)

    @staticmethod
    def _get_all(
        table: list[list[Any]], fields: list[str]
    ) -> list[dict[str, Any]]:
        return [DataModel._to_dict(record.copy(), fields) for record in table]

    @staticmethod
    def _get_one(
        table: list[list[Any]], fields: list[str], key: int
    ) -> dict[str, Any]:
        return DataModel._to_dict(DataModel._find(table, key).copy(), fields)

    @staticmethod
    def _edit(
        table: list[list[Any]],
        fields: list[str],
        key: int,
        changes: dict[str, Any],
    ) -> dict[str, Any]:
        if "key" in changes and changes["key"] != key:
            raise ValueError("record key cannot be changed")
        unknown = [field for field in changes if field not in fields]
        if unknown:
            raise ValueError(f"unknown fields: {unknown}")
        record = DataModel._find(table, key)
        for field, value in changes.items():
            record[fields.index(field)] = value
        return DataModel._to_dict(record.copy(), fields)

    def create_profile(self, **values: Any) -> dict[str, Any]:
        """Create a Profile record."""
        return self._create(self.profiles, PROFILE_FIELDS, values)

    def get_profiles(self) -> list[dict[str, Any]]:
        """Return all Profile records."""
        return self._get_all(self.profiles, PROFILE_FIELDS)

    def get_profile(self, key: int) -> dict[str, Any]:
        """Return one Profile by key."""
        return self._get_one(self.profiles, PROFILE_FIELDS, key)

    def edit_profile(self, key: int, **changes: Any) -> dict[str, Any]:
        """Edit a Profile record."""
        return self._edit(self.profiles, PROFILE_FIELDS, key, changes)

    def create_query(self, **values: Any) -> dict[str, Any]:
        """Create a Query record, validating its Profile reference."""
        self._find(self.profiles, int(values["profile"]))
        return self._create(self.queries, QUERY_FIELDS, values)

    def get_queries(self) -> list[dict[str, Any]]:
        """Return all Query records."""
        return self._get_all(self.queries, QUERY_FIELDS)

    def get_query(self, key: int) -> dict[str, Any]:
        """Return one Query by key."""
        return self._get_one(self.queries, QUERY_FIELDS, key)

    def edit_query(self, key: int, **changes: Any) -> dict[str, Any]:
        """Edit a Query record, validating Profile when it changes."""
        if "profile" in changes:
            self._find(self.profiles, int(changes["profile"]))
        return self._edit(self.queries, QUERY_FIELDS, key, changes)

    def create_feedback(self, **values: Any) -> dict[str, Any]:
        """Create a Feedback record, validating its Query reference."""
        self._find(self.queries, int(values["query"]))
        return self._create(self.feedback, FEEDBACK_FIELDS, values)

    def get_feedback(self) -> list[dict[str, Any]]:
        """Return all Feedback records."""
        return self._get_all(self.feedback, FEEDBACK_FIELDS)

    def get_feedback_item(self, key: int) -> dict[str, Any]:
        """Return one Feedback record by key."""
        return self._get_one(self.feedback, FEEDBACK_FIELDS, key)

    def edit_feedback(self, key: int, **changes: Any) -> dict[str, Any]:
        """Edit a Feedback record, validating Query when it changes."""
        if "query" in changes:
            self._find(self.queries, int(changes["query"]))
        return self._edit(self.feedback, FEEDBACK_FIELDS, key, changes)

    def recent_feedback_projection(
        self, now: int | None = None
    ) -> list[dict[str, Any]]:
        """Implement the variant-26 full outer join/projection selection."""
        current = int(time.time()) if now is None else now
        threshold = current - 8 * 60
        recent_queries = [record for record in self.queries if record[1] > threshold]
        output: list[dict[str, Any]] = []
        matched_feedback: set[int] = set()

        for query in recent_queries:
            matches = [item for item in self.feedback if item[5] == query[0]]
            if not matches:
                output.append(
                    {"cache_hit": None, "exception": None, "tags": query[5]}
                )
            for item in matches:
                matched_feedback.add(item[0])
                output.append(
                    {
                        "cache_hit": item[6],
                        "exception": item[4],
                        "tags": query[5],
                    }
                )

        for item in self.feedback:
            if item[0] not in matched_feedback:
                output.append(
                    {
                        "cache_hit": item[6],
                        "exception": item[4],
                        "tags": None,
                    }
                )
        return output
