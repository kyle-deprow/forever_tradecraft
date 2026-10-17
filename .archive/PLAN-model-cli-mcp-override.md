# Remove an invalid per-call MCP entry from the bounded model adapter

A single real configured LunaAdapter.observe_viewport diagnostic failed before a
model request with invalid transport in mcp_servers.openaiDeveloperDocs. The
shared user configuration is valid: the exact pinned CLI lists its normal URL
entry successfully. Parent independently reproduced the actual cause without a
model call: --ignore-user-config plus -c mcp_servers.openaiDeveloperDocs.enabled=false
creates an incomplete server entry without a transport. Removing that override
passes configuration loading and reaches a deliberately absent output schema.
Evidence: .archive/executor-review/model-cli-mcp-config-reproduction.json.

Official OpenAI documentation confirms --ignore-user-config skips the user config:
https://learn.chatgpt.com/docs/non-interactive-mode#permissions-and-safety
The existing --ignore-rules, no tools/features and read-only sandbox remain.
Do not modify global/private Codex configuration, credentials, CLI/model pins,
authentication storage or the running game/controller.

Luna owns ONLY src/crowley/session/model.py (command assembly: remove the orphan
MCP override, append the prompt normally) and tests/test_session.py (existing
bounded-command contract and a focused meaningful regression as warranted).
No other production behavior, model prompt, timeout, feature disable, environment,
allowlist, capture, driver, source or documentation edits. User revoked AGENTS.md.
Preserve all existing edits; no commit/reset/stash/revert. Keep artifacts under
.archive/executor-review/model-cli-mcp-*.

Record before hashes/raw files, implement the narrow fix and update command
contract coverage. Run focused model/command tests under the strict existing
runner, scoped Ruff/format/compile/diff. Do not spend live model calls: parent
will repeat the actual adapter diagnostic after independent verification and Sol
review. The absent-schema local CLI reproduction is allowed because it cannot
reach a model request. Freeze the exact diff/hashes. Parent independently tests
and Sol reviews before the service/model diagnostic uses the modified adapter.
Native resource helper work is separately owned and may continue without source
conflict. No helper edits or GUI/service/config/kernel writes are authorized.

## R2: classify the pinned CLI's exact noninteractive stdin notice

R1 passed parent6focusedtests and SolREADY. The next single real adapter call
completed in5.4069s but was rejected solely for stderr
`Reading additional input from stdin...`. Pinned `exec --help` confirms piped stdin
is appended even with a positional prompt; DEVNULL is deliberately noninteractive.
There is no quiet/no-stdin flag. Do not introduce a PTY, suppress stderr globally,
change stdin, loosen version/tool/output/deadline checks, or modify user config.
Allow only this exact standalone informational notice for the pinned CLI, after
exit0; all other nonblank stderr, including this notice mixed with an auth/error
line or similar-but-different text, still fails. The existing strict JSON event
and unique typed-answer parser must still run and reject malformed output/tools.

The same two-file fence applies. Add meaningful subprocess-boundary tests with
real owned harmless fake-CLI children for exact notice acceptance and mixed/
unknown stderr refusal, malformed/tool JSON refusal unchanged. No live API calls
by worker. Parent will verify focused tests+actual CLI parse and Solreviewr2 before
another single actualmodel diagnostic. This changes a classified informational
case, not the error policy for unknown diagnostics. Record measured call duration
as a diagnostic only; it does not establish freshness/admission eligibility.
