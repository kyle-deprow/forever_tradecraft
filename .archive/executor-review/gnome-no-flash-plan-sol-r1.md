# Sol plan review: private GNOME Screenshot no-flash experiment

I reviewed the plan against the accepted GNOME capture implementation, its
executable-resolution path, the retained single-instance GApplication diagnosis,
and the native provider's freshness and cadence checks. I did not inspect the
desktop live, run captures or tests, change source or configuration, or operate
services.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

The plan has the correct experiment boundary. It requires the exact matching
distribution source and provenance before building, permits one reviewed
`flash = TRUE` to `flash = FALSE` change, and keeps the result in a private
build tree. It does not change the installed package, desktop settings,
Crowley source/profile, compositor, schema, decoder, capture bounds, or native
acceptance rules. Missing development dependencies stop at a recorded
feasibility result rather than silently broadening host changes.

The single-instance risk is addressed at the right stage. A private
`gnome-screenshot` client is not proof that its code serviced a request because
it can forward to the current `org.gnome.Screenshot` owner. Stage 4 therefore
requires a concrete parent-reviewed runtime proposal and proof of the genuine
bus owner's PID, executable, and reviewed artifact hash before results can be
attributed to the private build. Keeping the canonical application identity and
Shell API, while forbidding a changed app ID, forged ownership, alternate
backend, or caller-check bypass, preserves the relevant caller behavior. A
temporary service transition is allowed only when the proposal identifies the
actual screenshot process, records its initial state, bounds the transition,
and restores normal activation. This is an implementation gate within the
already authorized experiment, not a new user-approval requirement.

The later benchmark also has the correct acceptance limits. Its concrete Stage
4 proposal must pin the process-local executable-resolution mechanism used by
the unchanged production driver, verify the resolved real path and hash before
capture, set an exact capture count and wall-time bound, and state the normal
service restoration commands. Stage 5 already requires the production identity,
cross-process lock, asynchronous completion, crop, decoder, caller identity,
and fresh-frame checks, and rejects identity, permission, parse, late, or stale
results. The current driver resolves `gnome-screenshot` from the benchmark
process environment and rejects a canonical executable outside that allowlisted
resolution, so a reviewed process-local resolution can exercise the private
binary without changing the daemon profile or host installation.

The experiment is appropriately non-qualifying. Removing the measured 500 ms
flash wait may still leave the whole capture path too slow; the plan does not
infer otherwise. Ordinary stationary benchmark frames can establish timing
feasibility only. They cannot establish native resource qualification, replace
the exact ordinal/sequence checks, or weaken the required 0.75–1.25 second
cadence for the 100-frame native window. A separate reviewed production binding
is required even if the private benchmark is fast enough.

STATUS: READY
