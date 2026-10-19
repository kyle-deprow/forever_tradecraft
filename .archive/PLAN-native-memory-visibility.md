# Native memory visibility before another live measurement

Status: Sol plan review READY. Bounded diagnostic correction; no resource-policy change.

The installed release reaches accepted held100, then the bound whole-Wine-process
reset5 window rejects48,644,096-byte peak growth above16MiB. Final RSS is lower
than baseline. An ordinary active scan separately shows91,168,768-byte sampled
RSS range in109s; this is context, not a matched reset5 control or attribution.
The complete failed measurement is already durably archived. Do not rebuild it.

Existing bounded native trace omits decoded Lua heap and texture count. Source
inspection found pooled2048textures and bounded100-sample timing/timer state,
with transient serialization/compression/copy allocations but no proven leak.

## Ownership and scope

Luna may change ONLY src/crowley/session/daemon.py (the private diagnostic's
record_candidate method and None defaults in begin_attempt) and
tests/test_session_runtime.py. Work from installed
commitbe71895 or a descendant with exact accepted six source/test bytes; create
an isolated worktree and freeze all original pins before editing. No Git commits,
resets, stashes, GUI, service, config, addon, calibration, driver, producer,
controller, journal, helper, protocol, memory thresholds or GC changes.

## Implementation

Retain already decoded render.luaHeap, render.textureCount and render.updateP99Ms
in each existing actual-candidate diagnostic record as a closed copied shape:
`lua_heap` is None or exactly {method,available,before_kib,after_kib,net_kib};
`texture_count` is integer-or-None and `update_p99_ms` is finite-number-or-None.
Never copy arbitrary render mappings. Preserve the exact `available=false`
flag with its numeric zero sentinels when Lua heap is unavailable. Keep last16 attempts,
run-span/size bounds, source bindings, file privacy, failure-only persistence,
all original errors and every admission/timing/cleanup guard unchanged. No new
capture, process sample, reset, heap API, compression call or per-frame disk write.
Lua heap describes the previous completed publication; document this lag in the
private diagnostic field meaning and never label it a Lua peak or addon attribution.

Exercise actual persisted diagnostic output from a decoded fixture frame:
values match independently known render fields, later nested heap mutation cannot
rewrite prior recorded evidence, unavailable heap remains explicitly unavailable,
private last16 retention and original failure remain correct. Extend meaningful
existing diagnostic tests rather than duplicating implementation.

## Acceptance

Run focused observation/diagnostic tests in test_session_runtime.py and scoped
Ruff check/format/compile/diff. Parent reproduces affected tests, inspects exact
2-file delta and validates unchanged production paths outside diagnostic method.
Sol and actual CLI Opus review only this bounded patch before quiescent promotion.
No full100 or seven-model repetition for this diagnostic-only delta unless code
outside the diagnostic path changes. Existing results stay bound to old hashes.

After deployment, finish ordinary chain before one controlled, fully instrumented
native100 attempt, paired with ordinary context. Retain all existing source,
identity, memory archives and failure cleanup. No unchanged blind retries. A
failed controlled result remains failed;16MiB gate cannot be relaxed by this plan.
Any resource-policy revision requires a separate concrete plan and review.

Only one instrumented retry: metric drift yields a concrete optimization target;
stable metrics plus another whole-process breach requires a separate resource-
policy decision. A pass proceeds to qualification with variability retained.
