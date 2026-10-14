DONE — fixround3 ownership A is complete.

Changed only:

- `addon/Crowley/Scanner.lua`
- `addon/Crowley/Commands.lua`
- `tests/test_addon.py`

Implemented global timeout ownership semantics, complete cumulative owner identity comparison, validate-before-abort commands, and strict regressions.

Checks:

- `uv run pytest -q tests/test_addon.py`: **35 passed**
- `uv run ruff check .`: passed
- `uv run ruff format --check .`: passed
- `git diff --check`: passed
