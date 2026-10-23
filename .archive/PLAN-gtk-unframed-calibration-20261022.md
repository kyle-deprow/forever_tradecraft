# Certify the observed undecorated GTK calibration client

Input87 observed the production GTK client while alive: exact owned PID/title,
WM_STATE Normal, focused, IsViewable, 480x240 at1440,32; Motif decorations=0,
no _NET_FRAME_EXTENTS, direct X11 root parent0x374, metadata child1x1 at-1,-1.
The current verifier waits for frame extents and reparenting, so cannot accept
this stable native surface. Evidence:
`~/.local/state/crowley/executor-evidence/calibration-retry-20261022/input87-observed-failure-20261022T1740Z/`
and sibling `input-startup-observed-20261022T1729Z/startup-observer.json`.

## Scope and implementation order

Worktree `/home/dev/.cache/crowley/worktrees/gtk-unframed-calibration-20261022`.
Read CLAUDE and repository local-game-control/client-contracts skills.
Own only:

- src/crowley/session/calibration.py
- src/crowley/session/driver.py
- tests/test_session_native_regressions.py
- tests/test_session_input_diagnostics.py
- tests/test_session_native.py
- tests/test_session_driver_actions.py if ticket/certificate fixtures require it

1. Encode the observed undecorated root-child GTK layout explicitly in the owner
   certificate, ticket and sealed input evidence. Pin that layout before querying;
   do not turn failed framed validation into an automatic weaker interpretation.
   Preserve a separately validated framed variant only if required by existing
   legitimate callers; production undecorated creation must select its observed
   contract directly. Do not change WoW game-window ancestry verification.
2. Verify owned process/executable/start/title/PID uniqueness, actual viewability,
   configured geometry, decoration property and actual direct parent/root.
   Root is structural evidence only and MUST NEVER become an input target.
   Certify only real owned event-capable client descendants. Exclude the observed
   InputOnly user-time metadata helper; no arbitrary sibling or ancestor admission.
   Reject malformed/mixed identity facts immediately, not after readiness waits.
3. Carry the exact layout/root/ancestry facts consistently through driver issuance,
   revalidation, Guardian ticket use, evidence construction, fingerprint and final
   verification. Do not fake a managed frame by using client or root as frame.
4. Keep startup ownership/watchdog/reap/unregister, absolute10s startup budget,
   source attribution, actual pointer preflight, synthetic motion query/endpoint,
   click rate/curved paths, genuine human qualification and revocation unchanged.
   Preserve bounded startup-failure facts before cleanup if needed to identify a
   refusal; existing persistence must retain them without fabricated certificates.

## Required verification

Replay the exact retained live window properties/tree through actual creation/
verification and driver ticket/evidence composition. Include a real isolated GTK
client with real root-child geometry and no fake Mutter frame. Test valid observed
surface, root/sibling/helper-as-event rejection, wrong PID/start/title/decorations,
unexpected parent/reparenting, unmapped/late/malformed metadata, ticket/evidence
layout/root mutations, no dispatch on refusal, and reap/unregister on failure.
Keep existing framed and game-window strictness where that mode remains supported.

Run focused affected tests plus diagnostics and appropriate native producer/driver
integration. Broaden to the full affected files once source is final. Run Ruff
check/format and git diff --check before freezing. Publish exact hashes, commands,
results and remaining limitations privately; source must remain frozen in review.
Sol reviews code and actual contract regressions independently; root reproduces
focused checks and promotes only reviewed bytes at a safe live boundary.

No implementer host GUI/input, daemon IPC, restart, deployment, commit or unrelated
edits. GUI owner is PAUSED88/native=true/input=false/checkpoint absent, user is in
Stormwind AH. Root coordinates any collection, deployment and next live run.
No further live retry until accepted repair. Human and autonomous qualification
remain pending; offline tests cannot establish either.
