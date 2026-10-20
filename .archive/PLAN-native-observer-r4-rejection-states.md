# Native observer R4: explicit rejection-state closure

R1-R3 review rounds did not fully close window-state edges. Replace the broad
correction plan with this two-file task and explicit acceptance table. This is
source-only work; no deployment/live action or admission-policy relaxation.

## Ownership

Existing Luna owns ONLY `native/x11_identity_observer/src/main.rs` and
`tests/test_x11_identity_observer.py` in the isolated fix worktree. Other eleven
approved candidate files remain frozen at final-manifest-r3d, including the
corrected cancellation test and all Python production code. Final manifest STILL
contains the same thirteen approved source files, including daemon. No additional
files/dependencies, public protocol/addon/telemetry changes or production test
hooks. No commits/reset/stash/revert, GUI/live capture/input/IPC/services/config/
DB/kernel actions or external messages. Owned offline Xvfb/process fixtures only.
Root owns plans, integration, review orchestration, installation and Git.

Read both R3 reports, prior plans and compact client-contract skill. User's broad
work authorization persists; do not stop for routine permissions. Preserve all
identity/cadence/ordinal/timestamp/CRC/resource/Guardian/cleanup/source guards.

## Two source corrections

1. `wm_state_focus`: raw focus0/None must return typed error before any active
window substitution. Actual vendored xdotool refuses it, even if the root active
window still points at the game and even with require_foreground=False. Preserve
nonzero raw focus when there is no WM_STATE ancestor and all existing exact
WM_STATE normalization. No arbitrary expected-window mapping.

2. `verify_window_candidate` must distinguish deterministic invalid layout from
failed observation: `Result<Option<VerifiedWindow>, String>` or equivalently
explicit typed cases. Concrete tree/size/client mismatch => invalid candidate;
real XQueryTree/XGetGeometry failures on an ALREADY title/class/PID-matching
candidate => error propagated to the overall observation. Never `.ok()` away
matching uncertainty when another valid target exists. Retain tolerance for
unrelated transient non-target windows and all final selected-window/process
lifetime rereads. No X grab/input/caching/fallback in production observer.

## Required observable states

| State | Expected result |
| --- | --- |
| One fully valid game target | Accept exact identity/fingerprint |
| Valid target + deterministically invalid matching window | Accept valid target/count1 |
| Two fully valid matching windows | Refuse ambiguity |
| No fully valid target | Refuse |
| Valid target + matching candidate whose real tree/geometry query fails | Refuse uncertainty |
| None/zero raw focus + game remains active | Rust and actual vendored reference both refuse |
| Nonzero raw focus/no WM_STATE | Preserve established raw behavior |
| Descendant focus + client/outer WM_STATE | Normalize identically to actual pinned xdotool |
| Unrelated focused window + active game | Foreground guard refuses |

Arbitration precision: complete outer geometry BEFORE counting is the approved
new observer contract. Legacy reference counts before the final outer-size check;
valid target + second wrong-outer-size/right-child-size candidate can therefore
be accepted by Rust while old reference refuses. Document this intentional,
fully verified-target difference rather than claiming universal parity. No extra
Python/reference implementation edits. The close-race FD-baseline nit is coverage
only; existing real lifecycle/constructor FD tests remain, no new architecture.

## Decisive actual evidence

Add None-focus mutation using real XSetInputFocus(None, RevertToNone), keep
_NET_ACTIVE_WINDOW on game; assert actual pinned xdotool/reference AND Rust
refuse, including require_foreground=False, then restore real focus and succeed.

For matching query uncertainty, use an OWNED deterministic barrier after the
observer has read matching title/class/PID and before its tree/geometry request
completes. Destroy/change the fixture window at that boundary, deliver the actual
X server error, and prove whole observer refuses despite another valid target.
Retain ordered barrier/query/error evidence and restored fresh success. No mocked
returned facts, production hooks, assertion based solely on unstable sleeps, or
broad 'success OR failure' predicate. A small owned X11 request proxy can gate a
real QueryTree after matching facts and forward the genuine server response;
other equally decisive existing owned-fixture mechanisms are allowed. Keep all
fixture sockets/threads/children private, bounded and reaped. If a tiny helper
inside the test file suffices, do not build a general proxy framework. A preserved
R3 binary counterexample is useful to show the regression distinguishes old
suppression, but do not modify preserved old artifacts.

Run decisive new cases, full observer suite, private offline Cargo check/build,
rustfmt, scoped Ruff/compile/diff. No source target pollution. Do NOT duplicate
full13/broad matrix yourself: freeze only AFTER last edit/check, all13manifest,
exact new hermetic binary+manifest and requirement-to-test map. Root independently
runs fresh13 and fresh affected broad/runtime/static at final pins (Rust changed,
so previous12 composition cases cannot carry). Then Sol and actualCLI Opus review
this two-file delta plus necessary existing context at the same final13pins.
DONE only when both corrections and meaningful evidence are complete. No live
qualification claim. Report a substantive blocker if genuine deterministic
barrier evidence cannot be built within this scope, rather than substituting a
weak test or changing production behavior for the fixture.
