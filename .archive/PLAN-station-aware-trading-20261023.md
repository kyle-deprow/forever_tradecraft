# Phase 3: station/tool-aware trading and launch strategy

Execute after suite refactor; may overlap launch-target work only with disjoint
ownership and coordinated test-lock use. Read AGENTS.md, CLAUDE.md, active handoff,
umbrella plan and docs/TRADING.md first. Implement with Luna, review with Sol.

## Existing facts

Core Recipe already carries totems, totem_categories and spell_focus. Exporter
already persists them in migration-005 tables client_recipe_totems,
client_recipe_totem_categories and client_recipe_spell_focus. No new migration is
needed for these recipe facts. Paper-run capability persistence does require a
new migration; never edit migration 006. Trading Recipe/load_recipes discard them and
craft execution does not enforce them. Beta pair results therefore overstate
availability where stations/tools are missing.

## Owned files

`src/crowley/trading/api.py`, `accounts.py`, `data.py`, `execution.py`, `engine.py`,
`market.py`, `paper.py`, `report.py`, `__main__.py`, `strategies/crafting.py`;
trading tests and new `tests/test_trading_requirements.py`; docs/TRADING.md;
new `.archive/station-aware-trading-20261023/` artifacts;
new `src/crowley/server/migrations/009_paper_capabilities.sql` only for storing
canonical capabilities on paper_runs. Add new trading helper
module only if it centralizes requirements for both strategy and executor.
Parent owns docs/HANDOFF.md; report suggested strategy status instead of editing
it. No addon/session/
core/exporter/deploy/applied-migration/other tests edits. No commits or live effects.

## Behavior

Carry all three requirement kinds intact through recipe loading and validation.
Explicit immutable account/run capability representation distinguishes available
spell-focus IDs and tool-category IDs. Exact required tool item IDs must be held
without consumption; categories must be explicitly provided, not guessed from
item names. Missing station/category capabilities mean unavailable, not unknown
treated as success. Require every listed requirement; station IDs are numeric.

Use one central availability predicate for strategy filtering and executor gate.
Refuse unavailable craft before consuming reagents, click/time budget or cooldowns.
Strategies must not acquire reagents for uncraftable recipes. Unrestricted recipes
retain their current behavior. Validate capability IDs strictly (positive ints,
no bools); recipes with invalid requirement IDs fail rather than normalize away.

Backtest capabilities are explicit simulation assumptions; record them in report
metadata and bind paper runs/replay to them. Default capabilities are empty.
Expose CLI options if necessary to make configured simulation reproducible.
Do not change real-gold arming behavior or publish queues. Keep accounting and
strictly-past market information unchanged. Two professions is a launch character
constraint; do not silently erase historical multi-strategy backtest support.

## Strategy evidence

After meaningful gates pass, parent may run read-only beta pair backtests using
existing DB access without exposing credentials or mutating stored runs. Compare
realized cash and recipe availability, record capability assumptions, and select
a provisional two-profession launch portfolio. Never claim beta profits predict
launch. If data access unavailable report that precise limitation; do not reuse
ungated old results as though rerun. Expiry/post-size changes require separate
evidence and a separate bounded follow-up rather than unmeasured strategy tuning.

## Verification

Small meaningful cases: real loader preserves all requirement kinds; validation
rejects malformed IDs; strategy buys no inputs for unavailable recipe; direct
executor cannot bypass gate; refusal leaves balances/budgets/cooldowns untouched;
tools are retained; category and focus independently required; permitted craft
works and reports/paper bind capabilities. Existing recipe/accounting tests pass.
Migration 009 defaults historical rows to empty capabilities; old run engine
digests must still refuse ungated replay. Record canonical capabilities/hash,
strategy professions/weights, build/window/house/capital/demand/wind-down and
recipe availability counts so pair results are comparable. Keep the same four
strategy matrix (two crafts, dip_reversion, vendor_arb) for pair comparisons.
All pytest under machine flock, scoped Ruff, final default suite remains <180s.
During concurrent launch-target work, run focused trading tests only; parent runs
the final integrated default suite after both implementations stop editing.
Parent independently verifies; Sol read-only review. Report files, commands,
counts, limits and DONE only after actual implementation/verification complete.
