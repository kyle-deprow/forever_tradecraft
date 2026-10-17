# Sol plan review: GNOME no-flash next-cost instrumentation

This was a read-only review of
`.archive/executor-review/gnome-no-flash-next-cost-plan.md` against the accepted
stage-2 manifest, source, benchmark contract, and eight-sample result. I did not
build, execute, capture, send input, or change runtime state.

## Must-Fix

1. **The run count and retry rule do not match the released diagnostic scope.**
   At lines 132-134, the plan authorizes one capture and requires another review
   before a second capture if markers are incomplete. The released scope is at
   most two stationary instrumented captures using one frozen reviewed
   diagnostic build and script, with no hidden retry. Rewrite this as two
   predeclared diagnostic ordinals maximum. Retain every attempted ordinal and
   its exact marker/capture failure; do not replace, discard, or renumber a
   failed/incomplete observation. An identity, owner, capture, decode, or cleanup
   safety failure must still stop immediately. Marker incompleteness alone may be
   reported for the first ordinal and followed by the already-authorized second
   ordinal, but never a third.

2. **The new build boundary is not concrete enough to protect the accepted
   stage-2 artifact.** Lines 100-104 and 195-202 say to make a private fork and
   use names under the cache root, but do not designate a distinct immutable
   build directory or state how dependencies are reused. Name an exact new root,
   such as
   `/home/dev/.cache/crowley/gnome-no-flash-next-cost-r1`, and prohibit writes to
   `/home/dev/.cache/crowley/gnome-no-flash-stage2-r1`. Reuse the already cached,
   pinned Bookworm container/toolchain dependencies or rebuild them inside the
   isolated container; do not install host packages. Retain the exact base-image
   digest, source/archive and Debian patch hashes, false-flash patch,
   instrumentation-only diff, dependency list, build logs, `x11=disabled`, ELF
   facts, and resulting binary hash. The diagnostic harness must then pin that
   new path and hash rather than weakening the existing allowlist or overwriting
   the accepted binary.

3. **Structured stderr needs a strict diagnostic-only framing and parsing
   contract.** Lines 111-130 specify fixed records and say a wrapper may retain
   stderr, but do not define how records are distinguished from ordinary GLib,
   GTK, or failure diagnostics. Define one versioned literal prefix and exact
   fields for operation token, child PID, event name, and monotonic nanoseconds.
   The diagnostic harness should parse only those prefixed records, require the
   same PID/token, allowed event names, required cardinality/order, and
   nondecreasing timestamps, while preserving all raw stderr and reporting
   missing, duplicate, malformed, or out-of-order markers as diagnostic failure.
   Nonmarker stderr must never become timing evidence. Keep this parser in the
   frozen private diagnostic harness only; do not change the production driver's
   existing command/stderr acceptance behavior.

4. **The output acceptance rule asks for equality that separate live frames
   cannot provide.** Line 208 requires “unchanged output dimensions/CRC/pixels.”
   The HUD advances between live captures, so a different strict-frame CRC and
   pixels are expected and cannot be used as evidence of an image-path change.
   Replace this with per-capture evidence: unchanged expected dimensions,
   complete lossless PNG, correct bound identity, and a valid fresh strict schema
   frame with the normal boot/sequence/stationary checks. If source-to-output
   equality is desired, compare the Shell source pixels and final output pixels
   from the same single capture only; do not compare the two diagnostic ordinals
   or the earlier benchmark images. The existing strict-frame route is already
   sufficient for this timing diagnosis and avoids adding another image read.

## Should-Fix

1. **The persistent-owner discussion attributes the private child to deployed
   production.** Lines 176-179 say that “today the production driver starts the
   exact private child.” The accepted benchmark's process-local `PATH` starts and
   proves the private child; deployed production still resolves the stock GNOME
   Screenshot binary. State those facts separately. The reusable driver property
   is that each admitted command is tied to its exact child process group and is
   killed/reaped on timeout or cancellation. A persistent private owner would be
   a prospective change from the benchmark's one-child-per-request ownership
   proof, not a description of the current production executable.

## Nits

None.

## Feasibility assessment

The proposed marker locations cover the causal client-side boundaries needed to
separate GTK/application setup, the synchronous Shell call, Shell-PNG loading,
the asynchronous output open/save path, recent-manager invocation, and process
teardown. `CLOCK_MONOTONIC`, fixed child-local markers, the same canonical Shell
API, `x11=disabled`, the unchanged production capture/crop/decoder path, and the
existing owner and cleanup proofs can provide useful bounded evidence without a
profiler, alternate backend, fake gate, or changed runtime deadline. The result
will remain diagnostic and cannot replace the exact 100-fresh-frame resource
proof.

STATUS: NEEDS WORK
