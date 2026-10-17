State your exact model ID first; require claude-opus-5-5 or stop.
You are a read-only reviewer. No edits, tests, binary execution, captures,
D-Bus queries, input, builds or service/config changes.

This is a NARROW closure review of your completed R1 review:
/home/dev/repos/pegasus/.archive/executor-review/gnome-no-flash-next-cost-opus-r1.txt
R1 already audited and accepted all genuine GNOME source/build/event flow.
That binary and all C sources remain identical. Do not repeat that audit or
reread the whole baseline unless a specific changed line makes it necessary.

Review ONLY the final R4 harness/documentation delta and targeted test code.
Read final freeze-r4 and the R4 delta file named in the worker's report in:
/home/dev/repos/pegasus/.archive/executor-review/gnome-no-flash-next-cost-*
Canonical harness:
/home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark.py
R3 predecessor:
/home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark-r3-candidate.py
Parent also inspected R2->R3 and independently passed28tests; Sol R3 READY.
Read final plan/report/manifest only where needed to verify corrected claims.

Accepted corrections/arbitration:
- End after first complete timing sample; second ordinal only for pure absent/
  incomplete first marker stream. Safety failures stop; no third ordinal.
- Original backend exceptions expose no raw CompletedProcess. The accepted
  correction NARROWS the claim: explicitly unavailable failure stderr, no fake
  empty file/hash; preserve exception and don't claim failure-stage attribution.
  Success data is driver-decoded stderr text, not byte-exact stderr.
- Add pure interval derivation: contain all CLOCK_MONOTONIC markers within the
  command start/end; partition non-overlapping stages including pre-main/tail;
  upper-bound marker overhead only, no acceptance from subtracted numbers.
- For deferred recent-file writes, use your explicitly offered MINIMUM fix:
  document/label app_release->run_return as mixed GTK shutdown/recent-file flush/
  D-Bus/settings sync. No C rebuild and no new shutdown signals required. Do not
  infer that a persistent process removes that mixed bucket. Recent markers
  cover only lookup/parse/in-memory addition.
- Meaningful ordinal/interval/parser tests plus harmless --version emitter
  test; live parser still requires complete stream.
- Distinct receipt name/kind, accurate PATH+token and PIL verify/load labels,
  honest missing build timestamp/original invocation/network facts.

Intent remains timing diagnosis only, before honest native100 one-Hz proof;
no production, binding, game input or live capture changes authorized yet.
Check closure and new reachable regressions only. Do not manufacture marginal
findings or re-open accepted design. Give Must/Should/Nits with exact path/line,
problem and correction; end exactly STATUS: READY or STATUS: NEEDS WORK.
