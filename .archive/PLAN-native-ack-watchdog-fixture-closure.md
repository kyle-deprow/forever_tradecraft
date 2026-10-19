# Final native fixture safety correction

Status: parent approved, test-only scope after Sol R3 READY and actual Opus R2.
Production correction and all parent offline gates passed. Opus found no
production defect; its Should1 test-safety issue is accepted before release.

Luna may edit only tests/test_session_native.py and tests/test_session_runtime.py
in native-ack-source-r2-20261019. Other four final-R2 files remain byte-identical.
No GUI, service, protocol, producer, Guardian, addon, helper or runtime changes.

Replace fake active PGID999999 with a test-owned live process group. Finally
restore the three injected Guardian fields under its lock on every exit,
republish through _watchdog_state, then terminate/reap the owned holder. Retain
all pre-ACK refusal and artifact/registry assertions. Accept Opus nits: pin old
baseline to actual returned/protocol refusal and reduced to no error plus real
budget overrun; correct owner-validation comment to held100 and resume0.

Run three new typed refusal cases, corrected baseline, and scoped style/compile/
diff checks. Preserve full private output and freeze two new/all-six hashes.
Parent reproduces these affected gates and verifies production/operator bytes
and the seven-case path are unchanged. Prior full compiled100/seven-model
results remain bound to the preserved R2 pins, with this test-only delta stated.
Sol and actual Opus review only this bounded patch and cleanup context. No
repeated full100 or seven-model run unless the delta changes their behavior.

Full Opus R2 report: executor-review/native-capture-ack-opus-source-r2-review.md.
All three current findings accepted; prior deferred R1 nits remain deferred.
