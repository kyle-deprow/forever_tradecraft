# Sol review: model CLI MCP override r1

Reviewed only the two-file frozen delta, its command-security context, the local configuration reproduction, and the focused regression. I did not run tests, make a model call, change configuration, or inspect unrelated model/native helpers. The supplied parent result is six model tests passing with 54 deselected, plus scoped Ruff, format, and diff checks. No successful post-fix model request has yet been established.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

The one-line production change is correct. `src/crowley/session/model.py:210-235` still supplies the pinned model, `--ignore-user-config`, `--ignore-rules`, the neutral working directory, a read-only sandbox, ephemeral JSON output, the exact output schema and image, low reasoning effort, disabled hooks, and the full disabled-feature list. It now appends the prompt directly instead of creating an incomplete `mcp_servers.openaiDeveloperDocs` table through `-c`.

[Official Codex non-interactive-mode documentation](https://learn.chatgpt.com/docs/non-interactive-mode#permissions-and-safety) states that `--ignore-user-config` prevents loading `$CODEX_HOME/config.toml`. The removed entry was therefore redundant for isolation and harmful because it created an enabled-field-only MCP record with no transport. The supplied reproduction distinguishes those cases before any model call: the prior command fails configuration loading with `invalid transport`, while the command without the override reaches the deliberately absent schema check. Removing this argument neither changes global configuration nor enables the user-configured MCP server for this invocation.

The focused regression at `tests/test_session.py:1121-1128` requires the custom prompt to remain the final positional argument and rejects reintroduction of the exact orphan override. The adjacent command-boundary test at `tests/test_session.py:1102-1105` continues to require user-config/rules isolation and the Luna model pin. Together with direct inspection of the unchanged command assembly, this covers the behavioral fix without weakening the sandbox or tool boundary.

STATUS: READY
