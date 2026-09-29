"""Simple interactive REPL for the in-memory model."""

from __future__ import annotations

import json
import shlex

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
        try:
            parts = shlex.split(line)
            command = parts[0]
            if command.startswith("create_"):
                result = getattr(model, command)(**json.loads(parts[1]))
            elif command.startswith("edit_"):
                result = getattr(model, command)(
                    int(parts[1]), **json.loads(parts[2])
                )
            elif command in {"get_profile", "get_query", "get_feedback_item"}:
                result = getattr(model, command)(int(parts[1]))
            elif command == "recent_feedback_projection":
                now = int(parts[1]) if len(parts) > 1 else None
                result = model.recent_feedback_projection(now)
            else:
                result = getattr(model, command)()
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except (IndexError, KeyError, ValueError, TypeError, AttributeError) as exc:
            print(f"error: {exc}")


if __name__ == "__main__":
    main()
