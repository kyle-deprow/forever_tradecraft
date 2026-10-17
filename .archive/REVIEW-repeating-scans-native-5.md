# Native readiness review, round 5

Sol: MAJOR ISSUES. Human/GUI calibration remains withheld. Native suites pass60
cases, but real old-calibration-ticket input after revoke was reproduced.

## Must fix

1. ONE guardian admission fence must own game AND calibration epochs/tickets.
   Current separate driver calibration mutex admits an old ticket after guardian
   revoke closed generation and snapshotted groups. Real exec wrapper launched
   /usr/bin/sleep after revoker returned. Move calibration authority, validation,
   wrapper registration, final check/gate and revoke snapshot under same guardian
   fence. Never register mutating process with generation=None.
2. Every mutation needs capability BEFORE first input. GTK verifier directly
   windowactivates before epoch/observer, and initial synthetic focus/F13/move/
   click use generation=None,ticket=None. Make structural GTK verification read
   only; establish epoch/observer/certified target ticket before explicit focus.
   Backend must reject input-producing commands without current game authority
   or exact calibration ticket, not rely on callers. Separate strict owned-release
   authority after revoke. No optional mutation capability API bypass.
3. Watchdog receives whole planned key/button union before any press. Publish
   actual current holds dynamically from backend, not future characters. Keep
   PGID ownership separate and never release unowned human/future-action keys.
4. Anchor lacks retained capture path. Deleting image still passes validation.
   Seal absolute retained path; require exists/hash match at atomic one-use
   admission; retain for review. Bind client click point to actual model-crop
   bounds, not separate unrelated point and rectangle checks.
5. Actual preflight F13 has detail8 with locked modifier0x10,latched0,base0.
   Hard-zero calibration fails real host. Measure stable tuple during owned
   synthetic operation, seal it and pin runtime expectations. No runtime learning
   and no clearing user's modifiers. Model actual emission with measured locks.
6. Unresolved source7 pointer motion cannot just be learned as human or allowed
   by source alone. Implement controlled echo correlation by class/device/master/
   target/sequence/coords/deadline, seal proven mapping and use it only for exact
   runtime synthetic echo. Unrelated/outside/unproven events still revoke. Do not
   whitelist source7 because the preflight saw it; obtain positive proof in the
   controlled owned-window phase before game pointer input.
7. If terminate/reap fails, _run currently unregisters PGID anyway. Keep guardian/
   watchdog ownership until poll proves exit AND direct child reaped. Report
   bounded termination failure, never drop still-live process group.
8. Ready is published BEFORE GTK prompt update. Update actual prompt successfully
   first, then readiness event/status, no race for parent/user notification.

## Should fix

- XI2 observer and GTK helper need owner-death cleanup (registered PGIDs or
  equivalent parent-death mechanism), not normal-close only.
- Synchronize timer bookkeeping with calibration epoch lifetime; no stale retry
  timers/waiters outside common authority fence.
- Lead default model-anchor producer still constructs unsealed MeasuredAnchor.
  Retain actual capture and call native driver.build_measured_anchor using full
  actual facts/crop/bounds/current generation. No dependency injected-only proof.
- Remove unused empty native capture temp directory and double hashing.

## Required meaningful checks

Real old-ticket concurrent revoke/spawn with /bin/sleep and exact orphan cleanup;
all mutating command callsites denied without capability; first synthetic action
scoped before input; future planned keys absent from watchdog; deleted/changed
anchor artifact rejected; actual nonzero locked-modifier trace accepted only
with matching sealed expectation; unrelated source7 motion rejected while any
positive echo requires actual paired evidence; failed termination keeps registry;
prompt precedes observable ready. Green fakePopen/ticket-only tests are insufficient.

No GUI/input/services/private configuration/prodDB/commits during corrections.
Dispatch owner retains driver/guardian/newdispatchtests; calibration owner retains
calibration/inputevents/nativeownedtests; lead owns actual semantic producer and
daemon/CLI/model/docs/testintegration. Independent owner alone owns two regression
files. All newly required fixture facts must be complete; no live compatibility.
