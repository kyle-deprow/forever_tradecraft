# Crowley

Private auction house trading platform and addon for WoW Forever (launch 2026-11-04).
**Read `docs/HANDOFF.md` first.** It has the requirements, decisions, research, current
state and roadmap. `docs/ARCHITECTURE.md` is the technical reference.
Shared agent workflows live in `.agents/skills/`; see `AGENTS.md` for when to use them.

## Rules
- **No fallbacks.** Assume one way things work, encode only that, fail loudly, and fix the
  assumption if it's wrong. Record client assumptions in the HANDOFF §6 table.
- Never key items by name; use `itemKey` (`scanformat.py`). Never mix houses.
- Schema changes go in a new `src/crowley/server/migrations/NNN_*.sql`; never edit applied ones.
- Buying, posting and cancelling stay one click per protected action. Never automate input.
- Ask before committing, pushing, or destroying data.

## Commands
```sh
uv run pytest                     # add CROWLEY_TEST_DATABASE_URL for the DB tests
uv run ruff check . && uv run ruff format --check .
docker compose -f deploy/docker-compose.yml up -d --build
```
