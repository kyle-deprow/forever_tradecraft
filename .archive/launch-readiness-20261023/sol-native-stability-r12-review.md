# Sol native test stability R12 review

Date: 2026-10-24

Scope: read-only review of `tests/x11_startup.py`, `tests/test_session_dispatch.py`, `tests/test_session_keyboard_rehearsal.py`, `tests/test_session_native_regressions.py`, `tests/test_session_startup.py`, and `tests/test_x11_identity_observer.py` against `.archive/PLAN-suite-stability-20261024.md` and the Crowley native-client contract guidance. No tests were run in this review. The parent full-suite benchmark remains separate and pending.

## Findings

### Must-Fix

None.

### Should-Fix

None.

### Nits

None.

## Evidence

- `tests/x11_startup.py:55-96` acquires the shared lock before creating the displayfd pipe or launching Xvfb and retains it through exact display-number receipt and a successful `XOpenDisplay` against that owned display. Server exit, timeout, malformed display output, and unavailable X11 all fail closed. `tests/x11_startup.py:97-104` terminates the owned failed server and closes both pipe descriptors on every exceptional path.
- The helper returns from inside the lock context, so context unwinding releases the lock before any caller's test body executes. It serializes allocation/readiness only, not native test execution.
- Repository search found exactly six Xvfb creators under `tests/`, all routed through `start_private_xvfb`: three in `test_session_startup.py` and one each in `test_session_keyboard_rehearsal.py`, `test_session_native_regressions.py`, and `test_x11_identity_observer.py`. Their original argv, including screen dimensions and the keyboard rehearsal's `-extension GLX`, remain exact. There is no fallback display, environment fallback, blind readiness sleep, or global `Popen` patch in the helper.
- Every caller closes the returned X11 display handle and terminates/waits for its owned Xvfb process. The helper's failure cleanup uses terminate/wait with a kill/wait fallback, so failed startup does not leak a server.
- `test_session_dispatch.py:773-838` first proves the original generation's real process group has disappeared, then rearms a second generation and makes a fresh real `_run(["/bin/sleep", "20"], generation=first, ...)` attempt. It requires prompt `DriverError` rejection and no active backend process group. Static inspection of the implementation confirms the retained old-generation cancellation check occurs before the pipe/`Popen` path; activating the new generation does not erase the canceled-generation record. Thus the late request is rejected before spawn rather than merely observing completion of the earlier request.
- The supplied worker log `.archive/executor-review/suite-stability-r12-all-xvfb-final-1792836448.log` reports `8 passed in 32.17s` under 16 workers. This review treats that as supplied evidence and does not substitute it for the parent full-suite run.

## Integrity

The six reviewed files matched `.archive/launch-readiness-20261023/native-stability-r12-sha256.json` before and after review:

- `tests/x11_startup.py`: `ad8b5db467a5cb1b2886587a579c41a721b4925b4bd150332e12592dc6c35881`
- `tests/test_session_dispatch.py`: `1a6aa2ee9733954563fb659e242fa39dde8255d0b4ce15e0e7cb588d62189ba5`
- `tests/test_session_keyboard_rehearsal.py`: `85b2a8d80abcda784fadc65a3cae5bc0ee1d5d8319bc97d1da135dd90fe8a41d`
- `tests/test_session_native_regressions.py`: `52860bc9c8b4c648055036589e651138128109155ec1e10149cbcda2bfd4d857`
- `tests/test_session_startup.py`: `05840baa993a7057f6a7de7c82a5a8e716a7e402dce017c0d086ec8b877ed503`
- `tests/test_x11_identity_observer.py`: `ab50599da459186f2cbfc826dc835b0997dd2ecb312e83a52fd55a5bfd95bb8c`

## Verdict

**READY**
