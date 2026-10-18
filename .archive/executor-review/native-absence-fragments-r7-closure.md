# Native absence fragments R7 closure

This candidate is frozen from base `eb2c69ee2bd8aad8055abb90af294aac96d995b1` in `/home/dev/.cache/crowley/worktrees/native-absence-fragments-r7-20261018`. Exact base and candidate hashes for all six files are in `native-absence-fragments-r7-freeze.json`; only the daemon pure classifier and directly related regression tests changed. No lifecycle, IPC, driver, helper, addon, protocol, configuration, service, GUI, deployment, or git changes were made.

The classifier now recognizes the actual wire geometry: any complete aligned protocol byte is eight logical cells, each an exact flat 2×2 black or white cell, with both values present. This local structural fragment rule is independent of header survival and uses no global percentage. Existing majority header checks, fixed geometry checks, binary loading rejection, malformed size/mode handling, and ordinary positives remain.

The focused generated regression covers one-byte magic erasure, all four magic-byte erasure, whole first physical row erasure, and full 26-byte header erasure, each combined with greater-than-10-percent payload occlusion. The generated focused check passed `2 passed, 114 deselected in 1.79s`. The retained private evidence check passed `4 passed, 112 deselected in 2.94s`: all four production decoder `ProtocolError` negatives classify `False`, and all four supplied ordinary game-region crops classify `True`.

The eight retained image results are:

- `black-loading.png` — SHA-256 `3b93f26267630963185ee67d8020972faee108a7bca80db725817e4680c9955c` — classifier `False`, decoder `ProtocolError`.
- `encoded-header-and-payload-occlusion.png` — SHA-256 `d28917c2061dfb5f28ac28275d1e3a05c2f318e252e9d121d264c233408054ed` — classifier `False`, decoder `ProtocolError`.
- `encoded-entire-magic-and-payload-occlusion.png` — SHA-256 `f28413cf71925638edda9f45ab2f775b84a94a8c33210af0bcd47f8af5e01e06` — classifier `False`, decoder `ProtocolError`.
- `encoded-whole-first-row-and-payload-occlusion.png` — SHA-256 `87d321bbe2e04c99da66c238c58405de3f16b75f33eb0e98f82d9bcda25d0b6e` — classifier `False`, decoder `ProtocolError`.
- `ordinary-game-region-1.png` — SHA-256 `e6a047dd6817af06aef7b803370ea2a73433bbb0bf1eb51e42e5c94445eed9b6` — classifier `True`.
- `ordinary-game-region-2.png` — SHA-256 `7e92d021419f1548e77ba13dd29384b89d7557d4cb317a199dc92b5c7cd8ac6e` — classifier `True`.
- `ordinary-game-region-3.png` — SHA-256 `73bb8d6700dbc9c86629cedf992833458ebe16c6f144f8c1312000af82a2f64b` — classifier `True`.
- `ordinary-game-region-4.png` — SHA-256 `8af8b29fde3237066cb936d87766bf9e0b93dd0c4161af0a76a68c2c2091e801` — classifier `True`.

The four ordinary crops are retained availability checks from the parent evidence directory, not no-addon target proof or live qualification.

The final native suites passed `330 passed in 352.47s (0:05:52)`, exit code 0. The mode-0600 retained log is `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-absence-fragments-r7-final-20261018/native-three-suites-final-generated-guard.log`, SHA-256 `b27d1a240b088d1d14f3cddab4313c8103421441ce92d57994b446c9ceddb789`. A pre-generated-test final production run also passed `330 passed in 348.20s`; its retained log and hash are recorded in the freeze JSON. The final static log is `/home/dev/.local/state/crowley/executor-evidence/runtime-relink/native-absence-fragments-r7-final-20261018/scoped-statics-final.log`, SHA-256 `ef52491033e141c3155544a71cb5d144d629277dadeb632909fbdd17ec1cbde8`; Ruff format/lint, Python compilation, and `git diff --check` passed.

Runs used the authentic private Codex 0.162.1 binary SHA-256 `628e35487d888a28f0427fc37501da529dd3d81fcbad7a2c3421c1e8670d92e1`, private mode-0700 XDG runtime, and candidate `PYTHONPATH`; import origins and exact hashes are recorded in the freeze JSON. Parent independent verification and Sol/actual CLI Opus review remain pending. No deployment, promotion, live capture, native qualification, or unattended-operation claim is made.
