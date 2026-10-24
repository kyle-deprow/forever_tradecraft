# Bounded actual mail-loop composition proof

Luna test worker owns only new tests/test_session_mail_loop_composition.py and
evidence under .archive/mail-loop-composition-20261024/. Runtime producer owns
controller/daemon/CLI/model/journal and its existing tests; deadline producer owns
driver/pointer_execution and its two tests. No overlapping edits. Read the full
PLAN-mail-loop-20261023.md and shared policy/driver contracts before implementation.

Build a small real public-path acceptance proof, not another fake Owner/status
or private-controller-only test. Reuse existing read-only fixtures where useful.
Use actual WowClient Lua/Data.lua ACK loading, current rendered captures,
PixelDecoder, real SessionDaemon/SessionIPC and actual DesktopDriver/Guardian/
X11Backend.action. Do not stub driver.run, execute_route_walk, execute_world_click,
execute_executor_click, guarded AH open or the scheduler. Model the external
capture/input world at the established fixture boundary; each emitted input must
cause its actual modeled scene/pose/mail change. No scripted phase-index frame
swap, generic copied snapshot dict, fixed production coordinate, or global time
monkeypatch. Fixtures are offline models, not native launch qualification.

Start from an established repeat WAIT_DUE boundary whose exact controller ACK,
status UID and actual Lua-loaded ACK agree. Preparing that precondition need not
replay three complete prior qualification cycles. Keep the current packaged beta
identity/plan and strict independent route/native/camera/input gates intact.

Required default unarmed proof:

- default disabled; exact public mail_loop_start enables one explicit queue/seq;
- actual route-to-mailbox, retained measured mailbox-world hint, hover-confirmed
  mailbox press, real unarmed executor-button dry run and causal ordinal/receipt;
- actual return route while mail may still be open, fresh closed-mail truth,
  guarded AH keyboard interaction and fresh AH-open postcondition;
- complete archive/once-per-ACK, binding disabled, ordinary resume/reconcile
  with the actual Guardian rearmed before claiming WAIT_DUE; zero protected
  calls, arm commands, queue publication/reload or successor execution.

Required armed two-message proof may share the same small fixture:

- both arms are observed fixture data; reaching the mailbox waits for a separate
  exact fresh one-click confirmation; no automatic protected press;
- first public confirmed click -> actual mail_wait; ordinary polls and competing
  IPC do not emit input; real mail event -> mail_items and another fresh request;
- second public confirmed click, later asynchronous actual terminal event,
  exactly two physical executor clicks, no third completion probe; contiguous
  craft successor remains untouched; complete return/reconcile ownership.

Assert the fixed absolute cycle deadline reaches nested real entrypoints and
observe private receipts/captured bytes rather than only return codes. Existing
runtime/unit tests own broad failure matrices; avoid duplicating them as expensive
full cycles. Native subprocess admission is separately proved by the driver slice.

Public IPC shape is fixed in the main plan. Producer defects discovered by this
test are recorded precisely with actual error/phase/frame/input counts in the
worker's progress evidence. Never weaken the proof or edit production to force
green. Source-frozen test code can be complete while documenting real current SUT
failures; root assigns production fixes and repeats integration until green.

All pytest holds flock /home/dev/.cache/r-pg.lock with pinned CARGO. Run only
this new file, scoped Ruff/format/compile and diff check. Keep setup and routes
small; default suite still must remain under180s. No game/service/DB/deploy/
commits/arming/secrets/evidence destruction. Freeze only after final edits.

## Round5 parent fixture correction

The public run_once continuation now reaches AH preparation. Parent inspection
localized a lower modeled-game omission: _MailBackend.action calls real
X11Backend.action (correctly), but _run keyboard-steps only emits observer events.
It does not apply Return/open-chat, typed keycode buffer, submit/target/binding or
Escape effects that the old LifecycleBackend.action emulator supplied. The real
AH preparation waits for focused empty chat and times out before prepare_command.

Fixture owner may model these external game effects causally from actual emitted
lower keyboard args/plans, keeping real DesktopDriver/Guardian/X11Backend.action.
Do not call fake LifecycleBackend.action or preseed successful target/binding.
The actual emitted exact target/binding commands must produce readback, and real
CTRL-F12 input may open AH only after valid target/binding. Preserve genuine Lua
publication and fresh frames. This is test-only external-game modeling, not live
client qualification. Re-review after correction and parent reproduce.
