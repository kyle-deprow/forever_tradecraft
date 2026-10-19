# R9 private screenshot fixture isolation

Preserve frozen native-capability-transaction-r9-20261018 and its reports. Root
created native-r9-private-fixture-20261019 from fb129d0 with all seven exact final
R9 files copied. Only tests/test_session_native.py is writable; other six are
read-only. No production/helper/driver/Guardian/config/addon/GUI/service/git edits.

Parent reproduced a ten-second pre-owner_ready stall. Actual strace plus Luna's
read-only diagnosis identifies private D-Bus activation of desktop portals,
followed by a 25-second GIO wait. GTK/GIO environment flags alone did not fix it.
Parent's no-service-directory private bus plus NO_AT_BRIDGE=1 passed the unchanged
compiled composition test, with actual producer/GJS/GTK/Xvfb/decoder and original
deadlines. Private evidence native-r9-private-bus-parent-r3-20261019, 1pass8.68s.

Implement a small local fixture used ONLY by the two tests that call
private_shell_compositor. Create a private minimal session bus config with
EXTERNAL authentication, normal private session send/receive/own policy, and no
standard/included service activation directories (an empty private service dir
is acceptable). Pass it to owned dbus-run-session via --config-file. The GJS
service manually owns its name and needs no .service file. Set NO_AT_BRIDGE=1
only for the fixture so absent accessibility services do not pollute exact
primary stderr assertions. Keep real GTK and real protocol/capture paths.

If intercepting subprocess.Popen, use a SUBCLASS preserving original process
type checks, with __init__ changing only the owned private dbus-run-session argv;
a plain function breaks driver isinstance validation. Preserve all other args,
real spawn/registration/ACK/deadline/cleanup semantics. Do not weaken stderr
assertions, mock successful reservations, widen deadlines or change capture code.

Run the two affected actual compiled tests, not all353 native cases, plus scoped
Ruff/format/compile/diff checks. Six unchanged hashes and unchanged existing ASTs
outside the two fixture bindings must be verified. Preserve private0700 dirs and
0600 complete logs, commands/base/hashes/import origins and resource cleanup.
Root will run the final focused cases independently. This is test isolation
after a documented failure, not a new executor implementation or qualification.

Write only native-r9-private-fixture-{closure.md,freeze.json} in main's
.archive/executor-review. Parent owns source acceptance, final Sol/actual Opus
review, commits and promotion. No source acceptance/live gate claim here.
