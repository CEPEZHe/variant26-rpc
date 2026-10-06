"""Simple interactive REPL for the in-memory model."""

from __future__ import annotations

import json
import shlex
from typing import Any

from model import DataModel

HELP = """Commands:
  create_profile JSON
  get_profiles
  get_profile KEY
  edit_profile KEY JSON
  create_query JSON
  get_queries
  get_query KEY
  edit_query KEY JSON
  create_feedback JSON
  get_feedback
  get_feedback_item KEY
  edit_feedback KEY JSON
  recent_feedback_projection [NOW]
  help
  quit
"""

KEY_COMMANDS = {"get_profile", "get_query", "get_feedback_item"}


def execute_command(
    model: DataModel,
    parts: list[str],
) -> Any:
    """Execute one model command entered in the REPL."""
    command = parts[0]

    if command.startswith("create_"):
        return getattr(model, command)(**json.loads(parts[1]))

    if command.startswith("edit_"):
        return getattr(model, command)(
            int(parts[1]),
            **json.loads(parts[2]),
        )

    if command in KEY_COMMANDS:
        return getattr(model, command)(int(parts[1]))

    if command == "recent_feedback_projection":
        now = int(parts[1]) if len(parts) > 1 else None
        return model.recent_feedback_projection(now)

    return getattr(model, command)()


def process_line(model: DataModel, line: str) -> None:
    """Parse, execute and print one REPL command."""
    try:
        parts = shlex.split(line)
        result = execute_command(model, parts)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (
        IndexError,
        KeyError,
        ValueError,
        TypeError,
        AttributeError,
    ) as exc:
        print(f"error: {exc}")


def main() -> None:
    """Run the model in an interactive text mode."""
    model = DataModel()
    print(HELP)

    while True:
        try:
            line = input("variant26> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not line:
            continue

        if line in {"quit", "exit"}:
            return

        if line == "help":
            print(HELP)
            continue

        process_line(model, line)


if __name__ == "__main__":
    main()
