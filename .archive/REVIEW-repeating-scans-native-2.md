# Native readiness review, round 2

Sol verdict: MAJOR ISSUES. Non-game human calibration and game arming are not
ready. No supported safe execution path exists yet. Parent reproduced 221 tests
passing (15 DB skips); Sol reproduced 34 native tests passing. Green batch/fake
tests do not establish streaming or executable readiness.

## Must fix

1. CLI socket timeout is 5 seconds; calibration takes 100+ or 120 seconds.
   A timeout reports a nonexistent daemon while calibration continues and can
   overlap repeated requests. Provide a supervised single-flight operation and
   observable status/completion/error path, without losing pause responsiveness.
2. Human readiness exists only in memory, not daemon status. GTK prompts from
   creation before synthetic proof. Expose actual post-proof readiness and only
   then change the UI prompt; parent must observe that signal before user input.
3. Incremental XI2 parser emits a record only at next EVENT/EOF. Complete idle
   final KeyRelease/ButtonRelease remains buffered even after blank separators.
   Test an open pipe and deliver complete final records without another event.
4. Human completion checks presses then stops observer before releases arrive.
   Await all raw/delivered press/release pairs and validate exact details/order.
5. Ancestry parses every hex token in xwininfo, admitting root/parent as owned.
   Parse actual tree relationships and test root/parent rejection with true child.
6. Clean observer EOF does not revoke. Guardian arms before monitor startup.
   Establish observer liveness before arming; unexpected exit immediately revokes.
7. Multi-character typing is configured as a single key's four events. `/reload`
   revokes on its second character. Model exact per-character details/modifiers
   and watchdog ownership/releases, using production emitted event semantics.
8. focus_game skips begin_action and revoke cancels only when held state exists.
   Cancel active focus/process groups on takeover even without held keys/buttons.
9. close terminates watchdog after physical release failure; finish_action has a
   generation-check/held-state-clear race. Preserve independent release fallback
   until release success; synchronize generation and ownership transitions.
10. Construction RSS is still sampled after addon already created textures.
    Actual preconstruction observation must precede authorized external bootstrap
    or reload. Do not weaken the gate to premeasurement capture in docs.
11. Anchors are config coordinates/fingerprints relabeled by one generic world
    observation. Measure each actual named control in its actual visible scene,
    with reviewable screenshot/identity provenance. Provide executable production
    producer, no assertion wrappers or guessed coordinates.
12. Persisted native boolean is reused after process/boot/display/driver/hierarchy
    change. Revalidate bound evidence and invalidate appropriately. Persist full
    proof: event proof, Xauthority, identity/geometry, Wine prefix, native capture
    reference, boot/CRC/render/RSS results. Fingerprints must cover those facts.

## Should fix

- Delayed-action test uses an independent execution gate that prevents execution
  throughout response window; it does not prove a genuinely due action stopped.
  Its eventual generation check/dispatch also races. Exercise actual due action
  cancellation atomically without sending input outside the owned test target.
- Motion correlation positive fixture invents 4/4 master/source, unlike captured
  2/7. Keep unknown source 7 closed; obtain actual positive XTEST relationship
  before game pointer actions. Do not infer source from owned target alone.
- Native capture cleanup must run on failed calibration as well as success.

## Verified improvements

Geometry-translated GTK click, Wine identity separation and windowless counting,
origin checks, four-pixel cells, sameboot101frames, full in-memory event proof,
one stdout reader, retained pause evidence, runtime monitor replacement, process
group cancellation, and valid tracked release commands are present.

## Ownership and next verification

Native owner fixes driver/calibration/input_events/guardian and owned tests.
Lead fixes CLI/daemon/controller/addon/config/model/docs within existing fence.
Independent regression owner alone changes its two independent test files.
Coordinate complete interfaces and outcomes, not per-edit approval. Keep all
input/service/configuration/live evidence untouched during implementation.

Required negative checks include idle open XI2 pipe; exact xwininfo tree;
separately observable CLI readiness beyond five seconds; complete `/reload`
event stream; clean observer death; failed release at close; identity/boot stale
calibration rejection; preconstruction baseline before any render allocation;
actual control-specific visual provenance. Re-review before physical sampling.
