# Sol review: model CLI MCP override r2

Reviewed only the two-file r2 stderr-policy delta and its focused subprocess tests. I did not make a model call or rerun tests. The supplied parent result is 13 model tests passing with 54 deselected, plus scoped static checks. The earlier 5.4069-second call establishes that the pinned CLI emitted the classified notice and completed; it does not by itself establish post-r2 admission, freshness, or a successful adapter result.

## Must-Fix

None.

## Should-Fix

None.

## Nits

1. `model-cli-mcp-r2-freeze.json` records `accepted_exit0_stderr` as `Reading additional input from stdin\n`, omitting the three periods that are present in the actual constant, tests, observed stderr, and adopted policy. Correct the artifact value to `Reading additional input from stdin...\n` so the freeze describes the exact allowlist accurately. This does not affect production behavior.

The production policy is strict and correctly ordered. `src/crowley/session/model.py:682-695` checks cancellation and nonzero exit before considering stderr, then accepts only an empty string or the single exact `Reading additional input from stdin...\n` value. Unknown, mixed, near-match, repeated, differently terminated, and nonzero-exit diagnostics remain errors. Stdout still crosses the existing typed JSON/event parser after `_run_cli`; the stderr exception does not bypass malformed-answer or tool-event rejection.

The tests exercise owned subprocess boundaries rather than calling the parser alone. `tests/test_session.py:1131-1169` proves exact-notice acceptance with the pinned fake CLI version, `tests/test_session.py:1172-1191` covers unknown, mixed-auth, near-match, and repeated stderr, and `tests/test_session.py:1194-1244` proves the accepted notice cannot make malformed or tool-shaped answer text pass parsing. The r1 user-config isolation, sandbox, feature disables, model pin, deadlines, environment validation, and prompt assembly remain unchanged.

STATUS: READY
