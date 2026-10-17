# Sol review: private GNOME no-flash build and benchmark, R1

Review scope was limited to the completed private build and the proposed eight-capture benchmark described by:

- `.archive/PLAN-private-gnome-no-flash.md`
- `.archive/executor-review/gnome-no-flash-stage2-manifest.json`
- `.archive/executor-review/gnome-no-flash-stage2-build-report.md`
- `.archive/executor-review/gnome-no-flash-benchmark-plan.md`
- `.archive/executor-review/gnome-no-flash-parent-build-verification.json`

No live capture, activation, service, settings, configuration, or GUI operation was performed in this review.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

## Review assessment

The frozen build evidence is sufficient for the planned experiment. It binds the private binary to genuine Debian Bookworm GNOME Screenshot 41.0-3 source, the recorded source archives and Debian patch series, an isolated pinned container image, and a private host-owned prefix. The recorded production change is confined to the full-screen Shell screenshot call's `flash` argument changing from `TRUE` to `FALSE`; the window and area paths remain byte-identical. Building with `-Dx11=disabled` makes Shell API failure terminal instead of silently changing the capture backend. The manifest and parent verification bind the only private `bin` entry, its version, build ID, and SHA-256 (`45750c8dca51a5f6ec5584be0e807a29a60284cca8a1cb5d13b8a2f45fde6af9`). The build procedure did not modify host packages, GNOME settings, D-Bus activation, repository source, or production configuration.

The proposed process-local `PATH` is a legitimate exercise of the unchanged production executable resolver and allowlist. The benchmark additionally requires the resolved path and binary hash to match the frozen private artifact, keeps the accepted capture driver hash fixed, and forbids resolver, admission, output, or deadline overrides. It therefore measures the candidate through the real production capture path without weakening executable identity.

The D-Bus ownership contract is fail-closed. It starts only with `org.gnome.Screenshot` unowned, observes acquisition without prewarming or spoofing, and binds the owner to PID, process start identity, executable path, and artifact hash. A stock, changed, ambiguous, or fallback owner aborts the run. Subsequent command forwarding to the canonical `GApplication` is recorded rather than hidden, so cold and retained-owner behavior remain distinguishable.

The benchmark remains bounded to eight sequential captures with no retries or extra screenshots. Scheduling starts at least 1.1 seconds apart outside the measured capture path lets the ordinary one-hertz HUD producer advance without subtracting wait time from measured latency. A valid capture exceeding the experimental one-second target is recorded as slow and may be followed by the remaining bounded samples; invalid identity, transport, image, or frame evidence still stops immediately. This preserves production deadlines and prevents a slow valid sample from being mislabeled as capture failure.

Every accepted sample must retain the WoW process/window identity, exact private executable and D-Bus owner identity, PNG completion facts, and strict decoded frame facts: `FRESH`, stable boot identity, increasing sequence, stationary position, and zero speed. These requirements support timing feasibility only; the plan correctly withholds live native qualification and the separate 100-frame claim.

Restoration is bounded to the exact private owner proven by PID, process start identity, executable path, and hash. It forbids signaling stock or changed processes, requires the bus name to return to its initial unowned state, checks for leftover benchmark processes, and records cleanup failure without retry. Host packages, settings, services, profiles, daemon configuration, and source remain unchanged.

STATUS: READY
