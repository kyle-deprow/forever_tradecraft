# GNOME no-flash next-cost R4 canonical build report

Status: **R4 canonical private diagnostic harness integrated; pending Sol/Opus
review.** No live capture, D-Bus activation, desktop input, profile/configuration
change, production source change, or rebuild occurred during R4 integration.
The accepted stage2 build, the private instrumented binary, and R2/R3 evidence
remain preserved; only the private harness and its review documentation were
promoted to the canonical R4 paths.

## Provenance

- Diagnostic cache root: `/home/dev/.cache/crowley/gnome-no-flash-next-cost-r1`.
- Private executable:
  `/home/dev/.cache/crowley/gnome-no-flash-next-cost-r1/prefix/bin/gnome-screenshot`.
- Private executable SHA-256:
  `b988bc4c49251c7951805b0af6ad942dd82d50052feffd338f5f6b72d43b025c`.
- Version: `gnome-screenshot 41.0`; ELF Build ID
  `9c7c8653a6f204fc281e74810b162ce12bf649e4`.
- Accepted stage2 executable remains SHA-256
  `45750c8dca51a5f6ec5584be0e807a29a60284cca8a1cb5d13b8a2f45fde6af9`.
- Upstream GNOME 41.0 archive SHA-256:
  `4adb7dec926428f74263d5796673cf142e4720b6e768f5468a8d0933f98c9597`.
- Debian source archive SHA-256:
  `3d185c0d1e8aab8381b9d530f12b4ae4c1049bd5054768197169a95fe2df5b9d`.
- Debian source descriptor SHA-256:
  `978f230fcd1d167a1368efedbf69ebfd963f12abf85ee84cddd29ee590815f2c`.
- Build image: `debian@sha256:2c037a04925515fdd6ea85ea14a682d0e79931f5e9f5d07b6dbfc6ba12f9e858`.
- Build configuration: `--buildtype=release -Dx11=disabled`.
- Build dependencies were installed inside the isolated container only; no
  host packages were installed. The prior build used bridge networking through
  apt update/install, Meson configure, compile, and install; no host source,
  display, repository, or credential mounts were used beyond the private cache
  root. The original Docker invocation was not retained.
- The accepted full-screen Shell `Screenshot` flash argument remains `FALSE`;
  window and area flash arguments remain unchanged.
- The private source diff is limited to the four C files and marker header
  recorded in the canonical manifest. The R4 pass did not rebuild that source.

## Canonical R4 harness

The canonical harness is
`/home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark.py`.
The tested R4 candidate is
`/home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark-r4-candidate.py`;
both are byte-identical at SHA-256
`29b9ebf15705b68cbb43756b266e076700d2f845ab7ef405959264387d4ef0c6`.
The canonical manifest is bound to the canonical path and this same digest.
The R2 canonical harness, plan, report, and manifest are preserved under the
`*-r2-preserved` paths, and the R2/R3 freeze/review artifacts remain unchanged.
The exact R2-to-R4 harness delta is retained at
`gnome-no-flash-next-cost-r2-to-r4.diff` and is included in the final freeze.

R4 corrections are bounded and private:

- A complete first marker stream ends the run. A second ordinal is consumed
  only after an otherwise-valid first attempt has an absent or incomplete
  marker stream. Malformed, mid-line, extra, unknown, cross-token, cross-PID,
  out-of-order, or non-monotonic markers are nonretryable.
- Successful `CompletedProcess` attempts retain driver-decoded text stderr; it
  is not represented as raw bytes. When unchanged production `X11Backend._run`
  raises, it exposes no `CompletedProcess`, so the receipt records stderr as
  unavailable, preserves the original exception, and does not create an empty
  fake artifact or claim failure-stage attribution.
- `derive_intervals()` uses marker nanoseconds and Python `time.monotonic()` on
  Linux `CLOCK_MONOTONIC`, requires command-boundary containment, exact order,
  no overlaps, and an interval sum equal to command elapsed time. It emits
  semantic adjacent intervals, `pre_main`, and `post_run_return_tail`.
  `sampled_empty_pair_total_s` and `sampled_empty_pair_max_s` describe only
  three explicitly identified empty marker pairs; they are not a bound for all
  marker instrumentation and no unmeasured pass is subtracted.
- `run_return` is the `g_application_run` return marker. Deferred
  `g_autoptr` cleanup after it is reported as a separate tail. Recent markers
  cover app lookup/parse/in-memory add only; `app_release` to `run_return`
  includes shutdown work and is not presented as removable startup cost.
- The manifest uses receipt schema 3 and kind
  `gnome-no-flash-next-cost-diagnostic`; any future live receipt directory must
  use `gnome-no-flash-next-cost-benchmark-*`. Process-local PATH and token
  injection are recorded while inherited XDG/GSettings variables remain
  unchanged.

## Offline verification

The exact canonical commands and retained final logs are:

```text
python3 /home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark.py --self-test
# 32 tests passed
python3 /home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark.py --self-check
# PASS
python3 -m py_compile /home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark.py /home/dev/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-benchmark-r4-candidate.py
# PASS
```

The offline tests cover complete-first-stop, incomplete-first retry and
second-incomplete refusal, failure precedence, strict marker token/PID/order/
cardinality and prefix placement, interval containment/order/sum/semantic
labels, unknown events and PID changes without an expected PID, the actual
compiled private `--version` marker prefix without display or bus activation,
and canonical manifest/binary/driver/source binding. No test activates a
screenshot or performs D-Bus, desktop, game, or native operation.

Final candidate logs are retained under
`~/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-r4-candidate/`;
canonical logs are retained under
`~/.local/state/crowley/executor-evidence/gnome-no-flash-next-cost-r4-canonical/`.
No live marker stream or frame was collected. This report makes no one-Hz,
native-100, or production qualification claim.
