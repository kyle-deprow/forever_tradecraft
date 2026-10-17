# Luna review: native construction isolation, Stage B R3

Plan reviewed: `.archive/PLAN-native-construction-stage-b-r3.md`
Verified SHA-256: `cc3892cff429d49ab48398926cf2351cecb20a9460fd5bbcfc23d222fed45784`

Review basis: Opus R2 report SHA-256
`631c80d26fa3950734597c22150632b88eac7e7686aaaf33ae80e7eddeb98892`, Luna R2
report SHA-256
`d0e0c2504356574a2bd7d8c255670ffb4c42d2339d18a7fb2965b4827e3f7d32`, current
addon/session interfaces, the local-game-control input-release contract, and the
read-only private helper provenance record. No tests, builds, GUI/input, or live
actions were run.

R3 closes the prior review findings about SavedVariables timing, helper ownership
and phases, recovery after malformed markers, sealed post-reset absence evidence,
pre-reload controls, handshake ordering, deadlines, reload recovery, independent
scanner/logout fences, and the old helper provenance mismatch. The three source
slices can be implemented and tested offline. Real control callbacks and templates
are correctly left as post-implementation live qualification gates; the plan makes
no claim that those callbacks, input, or a human-operated trial have already been
verified.

## Closed findings

- **SavedVariables and construction timing (Opus Must 1):** Core decides in its
  first `ADDON_LOADED` handler and Agent chooses its boot path in the later handler
  (plan 23-53). This matches Core's actual initialization at `Core.lua:110-116`,
  the handler insertion order at `Core.lua:85-107`, and TOC order with Core before
  Agent. The addon slice pins the order in the harness and covers ordinary
  publication.
- **Named actor and reachable controls (Opus Must 2):** The versioned operator tool,
  fixed chat sequence, daemon admissions, pre-reload control panel, and finalize
  admission now name who acts and when (plan 111-159, 161-217, 255-305). The
  existing CLI only exposes generation-bound `native-bootstrap` and
  `native-calibrate` today (`cli.py:118-133, 809-812`); adding the separately named
  deferred interfaces alongside them is a concrete offline slice. The plan leaves
  the existing bootstrap contract unchanged.
- **Recovery across operation boundaries (Opus Must 3 and Luna R2 Must):** Recovery
  no longer depends on the old generation and explicitly covers malformed markers,
  daemon/helper restarts, and post-finalize cases (plan 220-253). Restore replaces
  malformed values with a canonical `restore_pending` record using a daemon ticket,
  and success is established by an ordinary boot before owner resume (plan 54-85,
  128-150, 231-253). This closes the R2 non-table/missing-token dead end.
- **Post-reset absence evidence (Opus Must 4):** R3 seals the second capture's path,
  digest, identity, and completed time before release, uses one native clock, and
  retains the five-second checks with boundary tests (plan 183-198). This fits the
  runner's existing order: its preconstruction callback binds the reset baseline
  before it returns to construct polling (`calibration.py:4426-4476, 4551-4555`),
  whose daemon provider has a 30-second frame deadline (`daemon.py:1378-1380`).
- **Pre-reload exit and callback checks (Opus Must 5):** Defer creates controls in
  the ordinary load; Construct is inert while armed; Restore remains available in
  deferred/error/malformed states (plan 111-159). The callbacks and positive/
  negative templates are explicitly future live gates, not prerequisites for
  authoring the addon offline.
- **The six Opus Should-Fix items:** R3 spells out the handshake sequence (172-185),
  publishes and checks a bounded click deadline (200-217), persists
  `restore_pending` before `ReloadUI` and waits for the next ordinary load
  (128-150), defines malformed-record recovery (54-85, 231-253), separates native
  and logout fences while preserving the legacy public phase (90-109), and
  reconciles the exact d553/bf79 provenance delta while pinning the new tool in
  receipts (255-305, 347-359). The two prior nits are also closed: unrelated
  SavedVariables are tested against unchanged wire bytes (plan 94-96, 321-327),
  and capture/release comparisons use one clock (183-198).

## Must-Fix

1. **The ordinary failure path cannot enter the planned recovery admission.**
   `recovery-begin` requires `PAUSED` with no active operation (plan 222-225),
   while the `recover` tool mode is limited to admitted recovery and one Restore
   click (plan 293-295). In the current daemon, a failed native calibration records
   the operation error and finishes it at `daemon.py:4770-4795`; it does not pause
   the controller. The controller changes out of `NATIVE_CALIBRATION` only on the
   successful `native_calibrated` path (`controller.py:1457-1488`). Thus the common
   timeout/measurement-error case has no active operation but remains
   `NATIVE_CALIBRATION`, so `recovery-begin` must refuse and the fixed recovery
   mode cannot restore it. Add one explicit, guarded transition before recovery:
   either have the tool issue and verify the existing generation-bound `pause`
   request before `recovery-begin`, or let recovery-begin atomically pause/revoke
   only an exact terminal native-error operation. Cover this state and prove no
   Restore input occurs if the pause/revocation step fails.

2. **The helper does not cover release if its owner process dies.** R3 requires
   press ownership and unconditional release and tests a normal injected failure
   (plan 282-284, 354-358), but a Python `finally` cannot run after SIGKILL or owner
   death once XTEST has delivered a key/button-down. The applicable
   local-game-control contract explicitly requires an independent watchdog and
   exact key/button releases (`.agents/skills/local-game-control/SKILL.md:80-82`);
   the reviewed private helper's `finally` path alone does not provide that
   guarantee. Specify a watchdog independent of the operator process, bound to
   the exact owned input and pinned release tool, that releases it on owner death
   without releasing unrelated input. Add an offline regression that kills the
   operator after an admitted press and proves the watchdog releases the owned
   key/button and clears its ownership record.

## Should-Fix

1. **Define the reservation lifecycle across preflight and recovery.** The plan
   issues bounded reservations from both `native-construction-prepare` and
   `native-construction-control-preflight` (164-168), then starts a separate
   recovery ticket from the same `control-preflight` mode (293-295). Recovery
   tickets have explicit begin/complete/cancel semantics (222-239), but the two
   earlier reservations have no stated consume, release, cancel, or expiry
   transition. Specify whether preflight atomically hands its reservation to
   recovery-begin or releases it first, and how prepare/preflight reservations
   expire on helper failure, generation/lease revocation, operation completion,
   or daemon shutdown. Test that the handoff cannot overlap with a second input
   actor and that each terminal path clears admission.

The three offline slices are otherwise concrete and appropriately bounded. Live
template capture, click delivery, `ReloadUI` callback behavior, installed-hash
checks, and sole-operator authorization remain release gates after accepted code;
they are not reasons to defer offline implementation.

STATUS: NEEDS WORK
