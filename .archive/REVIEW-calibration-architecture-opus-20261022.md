# Independent calibration architecture audit — 2026-10-22

Requested by the user; actual model `claude-opus-5-5`, Claude Code2.1.306,
read-only Read/Grep/Glob tools, no MCP, no model fallback. CLI exit0.
Canonical runtime reviewed atc252a3f with the isolated unmerged keyboard fix.
This is an architecture verdict, not implementation or live acceptance approval.
The report's time estimates and proposed acceptance targets are recommendations.
Original full output SHA256: `0d02c3863522acb650ef3adead5e090c5417a935c5038b9acd648e813c04bba3`.

---

Model identifier: **claude-opus-5-5** (Opus 5.5). This was a read-only audit. I used only Read, Grep and Glob, and wrote no files, including no plan file. I ran nothing and did not touch the game.

# Calibration architecture audit

## Bottom line

The calibration utility is overengineered for what you need. Nine human-input attempts (59, 61, 66, 68, 75, 80, 85, 87, 92) have all failed before the human prompt appeared. Every failure was in calibration-only scaffolding: the temporary GTK window, a pointer-placement precondition, or a Ctrl+A chord that only calibration uses. None was in collection, upload/ACK, or takeover detection.

The design also requires a fresh native recalibration and a fresh human sample after every daemon restart and after common blockers. So even a passing calibration would not hold up unattended. The rule that actually detects takeover is small and already in the code. Most of the rest is certification around it.

## 1. What calibration needs to prove vs. what it proves

**What your outcome needs** (428-item scan every 15 min, original data kept, upload + ACK, natural ≤1/s clicks, prompt control on takeover, deterministic with Luna for exceptions):

1. **Our input is identifiable.** Our injected input arrives from known virtual "XTEST" devices, and the user's keyboard/mouse arrive from other devices.
2. **Takeover works.** A real user key, click or mouse move stops automation fast, releases held inputs, and pauses durably.
3. **The status HUD decodes** from the verified game window.

**What the current process proves instead:**

- **Input gate:**
  - A temporary GTK window must be certified as a root child, with its InputOnly helper excluded (`calibration.py:2612–3350`).
  - The pointer must already be inside that window, because a "bootstrap warp" is forbidden (`driver.py:4075–4099`).
  - It then types the whole runtime command vocabulary, about 280 key records. The recorded stream must exactly equal a predicted one (`calibration.py:4110–4184`, exact count check at `:4139–4140`).
  - Finally a human sample is required within 120 s (`calibration.py:3648`, `:3946–3963`).
- **Native gate:**
  - A mutating operator types 8 fixed slash commands, including `/reload`, through a 12-state handshake (`tools/native_calibration_operator.py:60–75`, `:184–197`).
  - It records 100 updates and resets/measures WoW memory via `/proc/<pid>/clear_refs` (`calibration.py:5133–5224`, `:5470`).
  - The 16 MiB memory target is *not* gating (`controller.py:1807`, `calibration.py:1984–1988`), but the measurement protocol is.

**Where unrelated demands got tangled in:**

- **Anti-forgery of our own events.** Exact per-event prediction (`guardian.py:1319–1580`; design source `.archive/PLAN-repeating-scans.md:501–509`) guards against some *other* program injecting XTEST input. That is not a takeover need; takeover only needs "this didn't come from our devices."
- **Performance study inside a correctness gate.** The original design said the native gate sends *no* game input (`PLAN-repeating-scans.md:513–515`). It now mutates the game (SKILL.md:429–431). The same original design calls the explicit CLI pause the authoritative takeover mechanism, with XI2 monitoring as an extra signal (`PLAN-repeating-scans.md:530–532`). XI2 certification has become the gate that blocks everything.
- **Deployment coupled to calibration.** Any patch means a restart, which means a native cycle plus a new human sample. The pending plan says so itself (`PLAN-input92…md:69–70`).

**Your needs vs. requirements the codebase chose:**

| Your stated need | Added by the codebase |
|---|---|
| Collection every 900 s; original data, upload, exact ACK | 3 autonomous cycles with starts at seed/seed+900/seed+1800 (each ±5 s) and upload within 60 s (`REPEATING_SCANS.md:265–268`) |
| Natural curved clicks ≤1/s (`CLAUDE.md` rule) | Exact predicted XI2 stream for every synthetic event |
| Prompt control on takeover | A human sample after every restart, in a certified GTK window |
| Deterministic, Luna for exceptions | Native construction/memory gate driven by typed `/reload`s |
| Launch readiness | Sealed evidence bound to PID, start time, geometry and tool digest; reviews per incident |

## 2. Ranked causes of the repeated failures

### Established from code and records

1. **Every restart needs a human again.** A new controller process clears both gates (`controller.py:339–353`). `resume` then routes to NATIVE_CALIBRATION, then INPUT_CALIBRATION (`controller.py:2346–2360`). The input gate cannot finish without a live human (`calibration.py:3946–3963`). Unattended operation can't survive a deploy or crash.
2. **Invalidation by matching words in error text.** Blocks or revokes whose reason contains "boot", "client", "identity", "crc", "protocol", "display", "hierarchy" or "observer" drop *both* gates (`controller.py:2892–2897`, `:3909–3915`). One such reason is "client boot churn during reload" (`controller.py:1549`), and reloads happen in every cycle. Any similar hiccup then forces a full native cycle plus a human sample.
3. **One wrong prediction fails the whole run.** With exact-equality validation, any producer quirk is fatal, and it shows. The unused `select_chat_all` chord (`driver.py:6537–6546`) caused **input61** (argv/holds, HANDOFF:849–856) and **input92** (the extra Control release; `diagnosis.md:9–24`).
4. **The pointer and window preconditions are artifacts of the harness.** Requiring the pointer inside the GTK window without warping caused 4 failures: 59, 66, 75 and 80 (HANDOFF:839–845, 368–376, 404–412). Window-manager assumptions caused 85 and 87 (HANDOFF:261–288). The calibration then moves with one linear `xdotool mousemove` plus a click (`driver.py:4106–4137`). That is not the curved runtime executor, and it conflicts with the CLAUDE.md wording "never…move linearly."
5. **The human step comes last in a long chain.** It follows a mutating preflight, measurement and recovery (`daemon.py:9570–9571`), and then has a 120 s window. Your availability was used up at least three times (input68, 80, 87; HANDOFF:811–816, 398–410, 276–282). Calibration also asked you to center the pointer (HANDOFF:842–844).
6. **Calibration gates a runtime path that doesn't match where Arthur is.** The autonomous AH-open is hardcoded to `auctioneer_buckler` (Ironforge) (`driver.py:4727`, `:5014`, `daemon.py:6176`, `model.py:40`). It needs a Luna call on every reopen (ARCHITECTURE.md:147–149). The working Stormwind method (`/targetexact Auctioneer Jaxon` plus the interact key) is not in the runtime `ACTIONS` or `COMMANDS` (`driver.py:4690–4702`, `:4738`). Passing calibration would not unblock autonomy.
7. **The strictness doesn't cover the input that is actually sent.** The live native operator types `/reload` and clicks with no XI2 takeover monitoring; I found no matches in `tools/native_calibration_operator.py`.
8. **Tests can't reproduce the failures.** The private-Xvfb proofs have no window manager and use fixture identities (`test_session_keyboard_rehearsal.py:247–305`). They can't reproduce the Mutter/XWayland behaviour behind 80, 85 and 87, so offline green keeps diverging from live.

### Hypotheses (not proven)

- **H1.** input68's unexplained XI2 timeout was the same chord problem; the chord was still in the profile then.
- **H2.** Routine disconnects and maintenance will invalidate calibration often (see the disconnect at 16:39 and the "World refresh" notice).
- **H3.** Your physical and RDP input arrive through non-XTEST xwayland devices. One drill would confirm it.
- **H4.** Once armed, the pointer echo correlation has never run live and will produce new mismatches.

### Visible costs

- **Collection gaps** (nominal 900 s):

  | Interval | Gap |
  |---|---|
  | 274→275 | 2970 s |
  | 284→285 | 3187 s |
  | 285→286 | 3294 s |
  | 286→287 | 1660 s |

- **Native cycles:** six live runs (57, 64, 73, 78, 83, 90), plus failed runs 54–56. Each includes `/reload`s.
- **Code and tests:** `calibration.py` is 5,771 lines and the operator 5,288. Calibration-heavy tests total about 30k lines: 10,258 + 10,474 + 9,199.
- **Process:** about 70 `PLAN-native-*` files. The game-control skill is 458 lines, mostly incident lessons, against AGENTS.md:26–27.
- **Per-iteration loop:** diagnosis, plan, Luna, Sol, parent, promote at an ACK boundary, restart, native cycle, attempt.

### Essential safeguards vs. optional complexity

- **Essential:**
  - Guardian watchdog release, generation revoke, process-group ownership.
  - The 1/s click permit (`pointer_execution.acquire_click_rate_permit`), the curved Fitts executor and re-checking the target before pressing.
  - Game identity and focus checks; CRS1 decoding.
  - Durable no-replay after restart (`controller.py:2302–2320`); exact ACK; failing closed on UNKNOWN events.
- **Optional:**
  - GTK window certification.
  - Exact typed keyboard profile.
  - Per-process human sample.
  - Native construction, held/100 and reset5 memory gate.
  - Substring invalidation; ±5 s cadence qualification.

## 3. Minimum practical design

### Your steps

- **Once, about 2 min, while you're present:** run a "takeover drill."
  - The daemon makes a slow curved hover inside the game, with no click.
  - You move the mouse or press a key.
  - It reports the detection latency, that inputs were released, and that it paused.
  - The record persists. Repeat only if the XTEST device *names* change, or if you ask.
- **Each start (automatic, roughly 10–20 s, no game mutation):**
  - Game identity.
  - Exactly one "Virtual core XTEST pointer/keyboard" (existing `xinput_hierarchy` and `xtest_sources`, `calibration.py:3352–3385`).
  - Observer alive.
  - At least 3 consecutive valid CRS1 frames.
  - Key expectations derived from the measured keymap (existing `observe_keymap`) instead of typed. The runtime commands are single unshifted keys.
  - Any failure → BLOCKED with the exact reason. No fallback.
- **Handover:** touching any input stops automation. The rule already exists: non-XTEST key/button/motion revokes (`calibration.py:3733–3745`), and the Guardian does the same. To hand back, run `resume` or tell Luna. It reconciles from fresh telemetry and never replays an action.
- **Errors:** a single BLOCKED reason plus the next step. Luna is called only for visual exceptions (disconnect, unknown dialog, AH didn't open).

### Keep, remove, defer — and the evidence behind each

| Item | Decision | Evidence that justifies it |
|---|---|---|
| Guardian/watchdog/click cap/curved executor/decoder/journal | Keep | Already the safety core |
| XI2 observer/parser | Keep | The input92 replay shows it parses correctly (`diagnosis.md:28–30`) |
| Per-restart human sample | Remove; replace with the one-time drill | The drill shows a non-XTEST key/motion revokes and releases. Classifying anything not from XTEST as human fails safe |
| Substring invalidation | Replace with typed causes (game PID/start changed, XTEST device set changed, display changed, observer died) | Reloads are normal; frame errors should block, not recalibrate |
| Typed keyboard profile and GTK window | Remove | Derive expectations from the keymap. Test by replaying the retained input87/92 traces |
| Native construction/held/100/reset5 gate | Defer and freeze as diagnostics | 287 assisted scans decoded correctly; per-frame CRC already proves decode; memory is already non-gating |
| Memory | Passive, read-only VmRSS/VmHWM reports, no `clear_refs` | — |
| Pointer echo pairing | Keep, at runtime only | Validate during the supervised first cycle, keeping traces |
| AH-open | Port the Stormwind `/targetexact` + interact-key method, checked by the HUD AH-open flag | Needed for autonomy. You'd need to approve the session-only binding |

### Suggested policy changes (read-only recommendations)

- Replace "genuine human input calibration + 3 cycles at ±5 s" (HANDOFF:629–633) with "one-time drill + a 24 h unattended run meeting your chosen on-time %, all data preserved and ACKed, zero unintended inputs." You set the threshold.
- Clarify that the CLAUDE.md click rule covers every automated click. The drill should use the runtime executor rather than calibration exempting itself.

## 4. Recommendation

**SIMPLIFY BEFORE CONTINUING.** This means replacing the two gate definitions while reusing the existing observer, Guardian, executor and decoder. It is not a runtime rewrite.

**Is the small patch plus one live rehearsal proportionate?** Not now.

- The patch is correct and low-risk: it removes the chord behind two failures. Keep it frozen and merge it with the simplification.
- A readiness-only rehearsal while you're away can't reach human acceptance.
- It still costs a restart, a mutating native cycle, and a 30–55 min collection gap based on the record above.
- The next restart or blocker would need you again regardless.
- If you choose to continue the current design anyway, the proportionate version is one attempt **while you're present**.

**Phases:**

- **Phase 0 (now):** Luna-assisted 900 s collection continues. No restart, no live calibration.
- **Phase 1 (offline, my estimate about 1–2 days):**
  - Startup self-check, typed invalidation, and a persisted drill record.
  - Native gate becomes the frame check; keyboard expectations come from the keymap.
  - Replay tests on the retained live traces; one review.
  - In parallel, port the Jaxon AH-open.
- **Phase 2 (about 15 min with you present):**
  - Deploy at an ACK boundary.
  - Run the self-check and the drill.
  - One supervised autonomous cycle; take over mid-cycle, then resume.
- **Phase 3:** Unattended operation, Luna only on BLOCKED. Measure the 24 h target and fix issues from retained traces.

## 5. Status

This rates whether the calibration architecture is fit to keep building on. It is not human acceptance and not code-review approval.

STATUS: MAJOR ISSUES
