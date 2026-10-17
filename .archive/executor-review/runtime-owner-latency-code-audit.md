# Runtime owner latency code-path audit

Status: read-only causal audit; no source or runtime changes. The timing input
is `.archive/executor-review/runtime-live-explicit-auth-performance-summary.json`
(SHA-256 `cac10e90f286f8e0041708196d1ba23f445cf25712dc700303c9dd3820a275e4`),
accepted source `3a95d89`, 26 completed timestamp pairs across the retained
16-run batch. These are wall-clock boundaries; this audit does not turn code
order into causal attribution.

## Observed boundaries

| interval | p50 | p95 | direct conclusion |
| --- | ---: | ---: | --- |
| owner entry -> producer request | 392.082 ms | 424.574 ms | pre-producer owner work is large |
| producer request -> lock | 0.074 ms | 0.083 ms | no material lock wait in this batch |
| lock -> ACK | 105.230 ms | 121.008 ms | pre-ACK setup/handshake is material |
| native capture | 41.991 ms | 58.053 ms | producer/capture boundary only |
| capture return -> owner `response_ready` | 395.297 ms | 420.772 ms | post-capture owner work is large |

The same accepted summary reports pooled application CPU p95 83.982 ms,
end-to-end wall p95 1.064735 s, ratio 7.8876%, zero model-call deltas, and no
eligible full eight-sample run. Rust therefore remains unqualified.

## Code-path mapping

The first ~0.4 s starts at `SessionDaemon.capture_paused_region_sample`
(`daemon.py:3720`) and ends when `X11Backend.capture_native_region` records
`request_started` (`driver.py:2817`). Before that boundary the owner performs
request/config/deadline and Guardian checks (`daemon.py:3753-3828`), creates
the private attempt directory (`daemon.py:3830-3843`), hashes and verifies the
seven runtime sources (`daemon.py:3847`, implementation
`daemon.py:156-248`), and resolves the live game identity
(`daemon.py:3852`, `driver.py:2233-2352`). The call continues through
`SessionDaemon._capture_native_region_for_identity` and
`DesktopDriver.capture_native_region_for_identity`
(`daemon.py:1965-2015`, `driver.py:6527-6568`); the backend performs another
identity resolution (`driver.py:2800`) before setting `request_started` at
`driver.py:2817`. Identity resolution scans `/proc` for matching game
processes (`driver.py:2171-2182`), then launches several allowlisted X11
utilities through the wrapper subprocess path (`driver.py:2243-2293`,
`driver.py:1227-1761`) and parses window ancestry. These operations are inside
the observed interval; their individual shares are not measured.

The 0.074 ms request-to-lock median shows that `_capture_lock`
(`driver.py:188-255`) normally acquired immediately in this batch. Its fixed
10 ms sleep (`driver.py:235-247`) is only reached on `flock` contention, so it
does not explain the observed median, though a contended future run could pay
it repeatedly.

The lock-to-ACK interval begins after `request_started`. Setup creates the
attempt directory, hashes the configured producer, copies/seals it into a
memfd, and creates socket/pipe gates (`driver.py:2842-2894`; executable read
and SHA-256 at `driver.py:94-154`). Guardian admission checks config/controller
state and spawns a fresh isolated Python wrapper (`daemon.py:3866-3874`,
`driver.py:2888-2943`, `driver.py:1602-1672`). The parent then waits for the
child `owner_ready` record and validates it (`driver.py:2947-2995`).
`_verify_admitted_process` runs before ACK and again immediately before it
(`driver.py:2997-3004`); each call checks `/proc` identity and hashes both
`/proc/<pid>/fd/<image>` and `/proc/<pid>/exe` (`driver.py:349-385`). Thus the
code path includes wrapper startup, JSON handshake, process-group checks, and
four sealed-object hash reads before `ack_sent` (`driver.py:3004-3006`). No
fixed sleep is present in this interval. The exact shares are unobserved.

The 42 ms native-capture interval is specifically the driver producer window
from child `capture_started` (`driver.py:3037`) to the raw producer
`capture_returned` (`driver.py:3092`). It covers start-record delivery, bounded PNG completion polling, output
digest validation, and process wait; the owner ACK precedes its start. It does not include the backend post-capture identity check, publication,
or attempt retirement that follow at `driver.py:3094-3193`.
`_json_record` can select for up to 100 ms when a protocol record is absent
(`driver.py:405-447`), and `_wait_for_complete_png` polls with up to 10 ms
sleeps (`driver.py:465-523`); neither was separately timed here.

The second ~0.4 s is measured from the projected producer
`capture_returned` at `driver.py:3092` to the internal `response_ready`
timestamp (`daemon.py:3992` or `daemon.py:4059`). The offline harness uses
`producer_attempt.capture_returned` first and falls back to the daemon field
only when absent (`offline_harness.py:1684-1688`), so daemon
`capture_returned` (`daemon.py:3884`) is a later boundary, not the interval
start for these receipts. The interval therefore includes the backend's
post-capture identity resolve, publication, and final process/directory
retirement (`driver.py:3094-3193`), then daemon PNG read/hash, receipt-byte
checks, sample construction/base64 encoding, and cleanup snapshot
(`daemon.py:3884-3942`). The daemon performs another full `resolve_identity`
(`daemon.py:3947-3949`, same `/proc` and X11 subprocess path), rechecks config
and controller admission (`daemon.py:3951-3962`), and may rehash the seven
runtime sources (`daemon.py:3977-3984`). Model counters and cleanup snapshots
are cheap local bookkeeping (`daemon.py:3986-3999`). The code sets
`response_ready` before durable receipt persistence at `daemon.py:4095`; this
interval therefore excludes final receipt write and IPC return, and the marker
must not be interpreted as durable response completion.

## Evidence versus inference
Directly observed: the five interval distributions above, zero model deltas,
the immediate lock acquisition, and the source-level timestamp ordering.
Strong code-path inference: the first interval contains both pre-capture
`resolve_identity` calls; the second contains the backend post-capture resolve,
retirement, and daemon post-capture resolve; lock-to-ACK contains
isolated-wrapper startup and repeated executable hashing. The receipts do not
time individual subprocesses, source-file hashes, PNG polling, or each
identity substep, so no one operation is claimed as the sole cause.

## Smallest follow-up profiling and safe opportunities
The next diagnostic should add local monotonic boundaries around
`_runtime_source_binding_for_diagnostic`, each `resolve_identity` subphase,
`_open_sealed_executable`, each `_verify_admitted_process`, owner-ready JSON,
and post-capture identity/config/source checks. Retain the receipt schema and
use one or a few authorized samples; no batch repetition is needed. A
deterministic review may consider reusing an already verified PNG digest for
the duplicate sample hash only if the receipt/output-byte binding is identical.
Removing identity rechecks, sealed hashes, Guardian admission, or final source
checks is not low-risk because those operations are the safety proof.

The reported 7.8876% CPU ratio is the accepted decoder/application interval;
owner and child CPU are unmeasured. A redesigned native helper using direct
X11 queries could potentially remove utility-process startup while preserving
semantics, but that is an architecture alternative, not migration evidence.
First profile owner/child boundaries and preserve the security proof; there is
no approved decoder Rust trigger or full-run qualification for either path.
