# Crowley agent guidance

Read [CLAUDE.md](CLAUDE.md) for project rules and [docs/HANDOFF.md](docs/HANDOFF.md)
for current state. Follow the user's current instructions and authorization.

Before operating the local game or troubleshooting game windows, read
[local-game-control](.agents/skills/local-game-control/SKILL.md). Include this path
when delegating game operation to a worker that does not inherit repository context.
Use a Luna worker for game input unless the user requests otherwise; delegate the
whole bounded outcome and keep parent oversight focused on milestones and blockers.

For shared producer/consumer changes, verify worker messaging tools and routing.
Workers may lack the parent's agent-name tools, and the app may reject peer task
messages even when their IDs are known. Use a small shared API contract file when
direct routing is unavailable; avoid relaying every API detail through the parent.
Starting new work in an idle worker requires a follow-up task; a plain message
only queues context and does not wake that worker.
After a worker reports DONE, send additional correction work as a follow-up task
and verify its status is running before waiting or reporting that work has begun.

For native client API, scan serialization, or Lua harness changes, read
[crowley-client-contracts](.agents/skills/crowley-client-contracts/SKILL.md).

Maintain reusable lessons in `.agents/skills/` so they travel with the codebase.
Consolidate observed mistakes into the relevant existing skill; create a new skill
only for a distinct workflow. Keep instructions short and exclude incident logs,
secrets, transient process IDs, and screen coordinates.
