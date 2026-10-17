# Sol review: runnable GNOME no-flash benchmark script, R2

This review was limited to the correction from the preserved R4 script
(`9a5ec2345974bebfb5fdad6f605190e026004f6962e8e75518784bd67b1b5e9c`) to the
current frozen script
(`c3c1e8707ffad75d37dc8e6e22dd22d6e32970ab33b0d6fea5dee6313fba0a8b`). I did
not execute the script or perform tests, captures, GUI operations, or service
changes.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

## Closure assessment

The R1 Must-Fix is closed. At
`/home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-benchmark-stage2.py:731-744`,
the preflight now requires `calibrationOperation` to be a mapping with a
nonempty string state, normalizes that state, and admits only `idle`, `complete`,
or `error`. Those are the production daemon's actual terminal values. The real
active values `starting` and `running` are rejected, as are missing, malformed,
or future unknown values, so a briefly free capture lock cannot allow an active
calibration worker through the preflight.

The delta adds direct offline cases for lowercase `starting`, retained lowercase
`running`, unknown, and missing states, while retaining acceptance of `error`.
The freeze records the parent-reproduced 22-test pass and build self-check pass.
No ownership, capture, timing, receipt, cleanup, or live-entry behavior changed
from the previously reviewed script.

STATUS: READY
