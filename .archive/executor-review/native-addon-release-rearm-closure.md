# Native addon release rearm closure

Status: frozen from the accepted final tree with the narrow Sol scheduling correction.

Finalize and restore-load previously released the private native fence while their lifecycle still blocked scheduling, so an open Auction House lost the release-triggered timer. After each checked publication transaction commits its final lifecycle and marker change, the addon now invokes the existing `SetNativeConstructionFence(false)` boundary again. This preserves the checked publication and rollback paths while causing no pre-commit scan request.

Real harness tests keep AH open through Construct/Measure/Resume/Finalize and through restore-load, then assert the final `native_construction_release` timer creation and strict inactive frame. The checked Finalize publication failure path keeps the fence armed and proves no release timer was created.

Verified:

- 244 addon and companion tests passed.
- 4 compiled atlas/frame smoke tests passed, with 63 deselected.
- Ruff check, Ruff format check, Python compileall, and `git diff --check` passed.

Only `addon/Crowley/Agent.lua` and `tests/test_addon.py` differ from the frozen final tree. No live qualification or promotion is claimed.
