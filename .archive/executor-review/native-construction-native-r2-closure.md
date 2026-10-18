# Native construction native slice R2 closure

Base commit: `e6e17bb42474b0251365590e61b87c9307b447fe`. Worktree: `/home/dev/.cache/crowley/worktrees/native-construction-native-r2-20261018`.

R2 corrects the finite operation envelope. The native runner invokes 103 provider calls: `construct/0`, `held/0`, `updates/1..99`, `held/100`, and `resume/0`. The deferred workflow adds the existing ten-second entry bound and thirty-second finalize bound. The outer admission is therefore exactly `10 + (103 * 30) + 30 = 3130` seconds. The seven-second constructor reserve remains inside the construct provider deadline and is not added to this outer budget. No individual provider, freshness, reset, update cadence, addon-release, or finalize deadline changed.

The composed regression now advances a complete strict PNG runner beyond 127 seconds using legitimate 15-second held and resume waits, while each remains below its existing 30-second provider deadline. It completes all decoded fresh captures, reset5 windows, callbacks, finalize admission, and durable checkpoint assertions. A separate virtual-clock regression sets the clock exactly at 3130 seconds and verifies recheck refusal plus durable `recovery_required` preservation.

Checks:

- Native construction focus: `5 passed, 86 deselected in 39.82s`.
- Full native regressions: `91 passed in 63.54s`.
- Six-file Ruff check, format check, compileall, and `git diff --check`: passed.

Parent owns final six-file/full three-suite verification with the authentic pinned CLI subprocess environment, compiled cases, Sol review, and actual Opus review. This metadata makes no broader acceptance or live qualification claim. The exact R2 six-file hashes and base-byte hashes were generated programmatically and validated as 64-character lowercase SHA256 values in `native-construction-native-r2-freeze.json`.
