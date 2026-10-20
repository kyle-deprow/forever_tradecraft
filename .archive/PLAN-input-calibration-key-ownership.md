# Input calibration: preserve canonical key ownership

## Objective and evidence
Native57 and ordinary58 passed on gamePID1033131/start33665951. Input59 refused
pointer origin before readiness. A changed, monitored input61 reached its owned
GTK target after normal reconnect, then refused `desktop argv holds do not match
its sealed input plan`. Human readiness never occurred. Live trace records target,
pointer and terminal error, NOT per-action argv/holds. Offline installed-source
reproduction identifies select_chat_all: emitted `key -- ctrl+a`, owned steps
Control_L+a, validator derives ctrl+a and rejects. Preserve this distinction.
Main daemon is paused62/native true/inputfalse/checkpoint clear; no retry pending.

## Ownership and scope
Implement only in /home/dev/.cache/crowley/worktrees/input-key-ownership-20261020.
Own ONLY src/crowley/session/driver.py and tests/test_session_input_tool.py.
In driver.py restrict edits to synthetic_keyboard_profile's key/chord serialization.
Do not modify _run argv/holds validators, admission/ownership/watchdog/protocol,
calibration.py, controller/Guardian/input_tool, addon, templates, Rust, profile,
services or live desktop. Parent owns plan, Git, deployment and final verification.
No commits/reset/stash/reverting others. Luna implements; Sol reviews. No Anthropic.

## Implementation
1. Keep canonical physical keysyms from the sealed KeyboardProbeStep profile in
   emitted named-key/chord argv. Do not collapse Control_L/Control_R to ambiguous
   ctrl aliases or change metadata to claim an unverified physical key. Preserve
   modifier transition order, finite operation vocabulary and exact ticket binding.
2. Keep argv-derived hold equality strict. Mismatched/missing/extra physical
   ownership must still refuse before process dispatch. No new input schema,
   normalization fallback, private ticket or widened allowlist.
3. Add a discriminating production-path regression: traverse actual
   synthetic_keyboard_profile -> _run validation/admission -> owned harmless
   pinned producer, with acknowledged watchdog ownership before GO. Do not replace
   _run, mock a matching validator, or bypass admission to make it pass. Exercise
   select_chat_all canonical Control_L+a, supported right-control distinction,
   ordinary keys and the finite actual runtime profile as appropriate. Test
   revocation/metadata mismatch no-dispatch and cleanup with actual child handles.
   External X11 may use isolated fixtures; never live DISPLAY:0. Reuse existing
   ticket/Guardian/harmless pinned fixture interfaces instead of inventing seals.

## Verification and freeze
Use MAIN .venv interpreter with explicit worktree src PYTHONPATH or an isolated
venv; never reinstall editable packages into shared environments. Confirm imported
crowley.__file__ is in this worktree before tests. Keep logs private0600/dirs0700.
Run full tests/test_session_input_tool.py, relevant existing keyboard-profile
cases in tests/test_session_native.py, and tests/test_session_driver_actions.py.
Run Ruff/check+format, py_compile and git diff --check scoped to owned files.
Retain actual failures and cause/corrections; no blanket reruns or unrelated
Rust rebuild/suites. Freeze exact two hashes and report actual checks/DONE.
Parent independently reproduces meaningful cases before Sol review; fix/review
until READY. Parent verifies final source and stages exact owned files only.

## Deployment and continuation
Changing loaded driver.py requires a controlled session-daemon reload. Before
promotion, sole Luna owner verifies fresh ordinary quiescence/current process,
public pause/checkpoint clear and no active calibration/input. Parent preserves
native57 proof, stops only sessiondaemon, installs exact reviewed bytes, restarts
that daemon with gates invalidated, verifies config/other sources unchanged.
Do not carry native57's private seal across this reload. Fresh native100 + canonical
ordinary recovery must pass before monitored GTK human startup. Normal cached
reconnect/known Normal realm/Arthur remain authorized; no navigation/trading.
At actual readiness notify parent immediately; never synthesize human samples.
Then three new autonomous900-second full cycles remain required. Zero counted.

