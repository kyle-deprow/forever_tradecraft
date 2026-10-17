# Auxiliary review round 2

Sol verdict: MAJOR ISSUES. The owned addon suite passed 94 tests, independently
reproduced by the parent, but the following production defects remain.

## Must fix

1. An armed fence makes Scanner.Status emit blocked/logout_fence. Agent projects
   that into pending.blocked and the strict decoder rejects its reason. Keep an
   armed fence in an honest idle ready/scheduled phase, with the separate armed
   scheduleFence; do not weaken the decoder or allow item/owned phases at logout.
2. Plan validation accepts arbitrary 428 increasing IDs under a claimed canonical
   hash, and Agent projects top-level fields rather than the decoded scan body.
   Bind the complete actual decoded canonical plan to the shipped definition and
   hash, reject top-level/body mismatches, and project the validated actual plan.
   Do not invent an unverified client hash API or a compatibility path. Keep any
   necessary canonical representation compact and test it against the source
   catalog so changes cannot silently diverge.
3. The model parser accepts arbitrary/tool-bearing item.started payloads such as
   mcp_tool_call, web_search, and file_change before a valid answer. Require the
   exact supported lifecycle and payload shapes; reject all unknown/tool items
   at every event stage, not just completed events.
4. Lua heap sampling accepts math.huge, producing infinite fields and NaN net.
   Reject all nonfinite samples and emit the existing honest unavailable schema.

## Verification

Add regressions for armed-fence pixel decoding and idle eligibility; altered
same-length canonical plans and top-level/body mismatch; unknown and tool-bearing
started events; nonfinite heap samples; and the 128/129 UTF-8 byte chat boundary.
Preserve real 428-ID, pagination, depth, tie, incomplete and API tests.

Ownership remains the exact auxiliary ten-file fence recorded in the main plan.
No controller/native edits. Run the full addon suite and relevant model/CLI tests
with strict thread/unraisable/fork warning errors, scoped Ruff check/format and
diff check. Parent reproduces; Sol re-reviews stable files. No game input,
service activation or live performance claim is cleared by these checks.
