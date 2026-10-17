# GNOME no-flash next-cost R3 candidate (draft)

Status: candidate only; **not frozen or released for live execution**. R2
artifacts remain unchanged. No screenshot, D-Bus activation, desktop input,
service, profile, or build action was performed for this candidate.

## Narrow corrections

- The production loop now stops after the first complete valid marker stream.
  It consumes the predeclared second ordinal only when the first otherwise-valid
  attempt has an absent/incomplete marker stream; malformed/extra/cross-PID/
  cross-token/order/timestamp marker errors and owner/capture/decode failures
  stop immediately. The `sample_attempt_decision` helper is exercised by three
  new offline decision tests.
- Successful completed children retain raw stderr. When unchanged production
  `X11Backend._run` raises, it exposes no `CompletedProcess`; the candidate
  records `diagnostic_stderr_available=false` and the exact unavailability reason
  without writing a fabricated empty file or claiming failure-stage attribution.
  Original exception priority is preserved.
- Any future live receipt directory uses
  `gnome-no-flash-next-cost-benchmark-*`, separate from accepted stage2 names.

## Candidate identity

- R2 base harness: `/home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark.py` SHA-256 `86f977d6112e51f6d540c94c26914b6ea9ece33c58d6e28b5cf330fee6c32e38`.
- R3 candidate harness: `/home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark-r3-candidate.py` SHA-256 `70743fa2c6beddc4dd681d88d424a87905742130c9ecc1388351ec64f11e6c18`.
- Existing private binary remains bound to the R2 manifest: SHA-256
  `b988bc4c49251c7951805b0af6ad942dd82d50052feffd338f5f6b72d43b025c`.
- Candidate uses the unchanged production driver hash
  `14ae6be4a901a17e396e68ac4501238db3d1cc0118c8c34ad6f7107fbcfacfa7`.
- Candidate diff: `/home/dev/repos/pegasus/.archive/executor-review/gnome-no-flash-next-cost-r3-draft.diff` SHA-256 `9deb3683036d3d76c65046c7fbb15ebfbb7d60f1ad4b5e4132066f2fbc770047`.

## Offline verification

```text
python3 /home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark-r3-candidate.py --self-test
# 28 tests passed
python3 /home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark-r3-candidate.py --self-check
# PASS
python3 -m py_compile /home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark-r3-candidate.py
# PASS
```

Logs are retained privately under
`/home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-r3-candidate/`.
The candidate is held for parent, Sol, and Opus review; do not use it for live
measurement until separately released.
