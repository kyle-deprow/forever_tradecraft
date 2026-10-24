# Phase 2: one launch target

Execute only after phase 1 passes parent verification and Sol review. Read the
umbrella plan, AGENTS.md, CLAUDE.md, active handoff and client-contracts skill.

## Outcome

One strict packaged target definition drives operational client/build/interface,
executable/window class, product/flavor, locale, realm/house, and scan-plan
expectations. The checked-in target remains the verified beta target; never invent
November launch facts or operate the game. Launch becomes editing that definition
plus explicit generation/client-data regeneration and qualification.
The target includes strict absolute installation gameRoot and winePrefix values
(current verified paths are already in tracked deployment templates). Do not emit
machine paths to Lua. Staged config must actually rewrite the flavor folder,
session SavedVariables/Data.lua paths and wine prefix; copying companion.toml
unchanged does not satisfy game-folder parametrization. Preserve account-path
suffixes, companion state, unrelated pins/settings and secret environment use.

## Owned files

- New `src/crowley/data/game_target.json`, `src/crowley/core/game_target.py`,
  `tools/generate_launch_target.py`, `addon/Crowley/GeneratedTarget.lua`.
- `src/crowley/core/watchlist.py`, `src/crowley/core/client_data.py`,
  `src/crowley/core/scanformat.py` only operational target/policy coherence,
  `src/crowley/session/config.py`, `driver.py`, `protocol.py`, `evidence.py`,
  `src/crowley/session/controller.py` target-derived qualification/default budgets,
  `route_walk.py`, `src/crowley/session/daemon.py` route loading and target-plan derivation only,
  `src/crowley/companion/config.py` only target integration.
- `src/crowley/server/app.py` default scan-plan emitters only.
- `src/crowley/data/first_run.json` only generated target metadata if necessary.
- `addon/Crowley/Scanner.lua`, `Context.lua`, both addon `.toc` files.
- `tools/client_data_export.py`, `tools/client_data/app/Program.cs` only target args.
- Deployment example templates only; live `deploy/config/*` remain unchanged.
- New `tests/test_launch_target.py`; existing watchlist, addon, client-data export,
  session config/evidence/protocol/route tests only when target changes require it.
- `tests/test_executor.py` only explicit synthetic target fixture binding;
  `tests/test_server.py` real-addon fixtures and plan expectations.
- New `docs/LAUNCH_TARGET.md`; report handoff changes to parent instead of editing
  docs/HANDOFF.md (parent owns integration while other phases may run).
- New `.archive/launch-target-20261023/` artifacts.

## Requirements

Strict typed validation (unknown fields, missing fields, bool-as-int, inconsistent
builds/house fail). No runtime dependency on an external checkout/deploy directory:
wheel contains the target. Avoid circular imports between target and watchlist.
Single full build value; derive native build/version from it. No fallback target.

Derive count/hash/compact entries from the catalog's canonical scan plan. Generated
files use exact deterministic bytes; `--check` never writes, fails on any drift.
Explicit write mode may update generated source artifacts but must never overwrite
installed config, live Data.lua, SavedVariables, routes or private evidence. Provide
staged session/companion config rendering for launch deployment, preserving all
unrelated credentials/pins/calibration fields, with no automatic deployment.

Catalog build metadata is generated/checked against the target; generator must be
able to regenerate after a target edit rather than importing a loader that rejects
the old catalog before generation. Keep existing beta plan bytes/hashes unchanged
when target inputs are unchanged. Catalog item identities stay numeric/itemKey.

Load GeneratedTarget.lua before dependent addon modules and update `tests/wow_harness.py`
file ordering as necessary. Keep live scan wire/protocol shape and telemetry schema
unchanged. Replace operational hard-coded count/build checks; historical evidence
UIDs, prior build fixtures and route measurements stay historical. Reject using
routes measured for a different target build; do not relabel their kinematics.
For the existing unversioned route file, accept only its exact measured beta
provenance constant when the selected full build is the verified beta build.
Reject that artifact for any changed target. Future route-format redesign is
outside this phase; do not guess build IDs by parsing arbitrary prose.

C# exporter takes required expected full build from Python orchestration; preserve
offline install validation and pinned image/tool inputs. Distinguish parent install
root from the companion flavor directory. Preserve strict wrong-build failures.

No production timeout/click-rate changes. No game, service, DB mutations, commits,
pushes, stash/reset/revert, worktree deletion or evidence removal. Scope formatter.

## Verification

Meaningful small tests for validation, generated drift, alternate synthetic target
and plan size (proves values are consumed), loader/config coherence, addon loading,
exporter expected-build plumbing and route build rejection. Exercise real generator
`--check`. Tests under `flock /home/dev/.cache/r-pg.lock`, CARGO pinned, default suite
must remain green and externally timed <180s. During concurrent station work,
run focused owned tests only; parent runs the final integrated default suite after
both implementations stop editing. Scoped Ruff checks. Parent reproduces
checks; read-only Sol reviews complete scoped diff. Report exact commands/results and
remaining launch-only acceptance; DONE only upon completion.

## Follow-up fence (parent inspection)

Complete the operational count path through controller qualification and server
plan emitters; changing active catalog count must not leave an exact-428 gate.
Keep the required 900-second collection cadence as explicit fixed policy: reject
unsupported cadence changes at target parsing, rather than advertising arbitrary
cadence while old wire validation rejects it. Derive operational defaults from
the target and leave historical payloads/admission semantics intact. Sweep cap
must flow through controller defaults as well as addon/config.

Target schemaVersion must reject floats (including 1.0), and context region/ruleset
must be valid House values. Keep productDir a single relative flavor component.
Context also carries required nativeRegionId (verified beta 110). The addon must
match that native ID and the selected realm exactly, then use target region and
ruleset for every target, preserving explicit overrides and neutral detection.
Do not retain a beta-only target realm branch plus hardcoded launch realm maps.
An alternate generated artifact tree must include the selected packaged target,
not only new catalog/addon bytes paired with the old default target.
Use the tool checkout's existing TOCs as required templates; never fabricate a
minimal Interface-only TOC when one is missing. Preflight destinations before
writing: a custom output-root must not bypass protection of the actual checkout's
live deploy/config, installed ~/.config/crowley, or current/selected game roots.
Stage/config destination validation must happen before any artifact mutation.
Exporter --install may explicitly override a target-derived default for controlled
fixture/inspection inputs; the normal export command uses installation.gameRoot.

## Final review correction fence

Session load_config and CompanionSettings must reject stale explicit operational
identity/path values, not merely use target defaults. Session planHash/planJSON
must exactly match the target's canonical plan, not just each other. Preserve
direct dataclass unit seams; update fixture expected-target providers rather than
adding production skip-validation flags.

TOC generation always reads complete checkout templates and validates exactly
one GeneratedTarget.lua before Context/Scanner dependencies. Alternate output
trees need no pre-seeding. Staging requires SavedVariables/Data.lua keys; missing
keys fail before any mutation. Route admission compares selected target provenance
and artifact provenance to the verified beta fact, preserving the beta build fence.
The exporter supports only enUS today; reject other locales at target parsing.

The alternate-count regression must actually invoke snapshot validation and
consumer SavedVariables/Data.lua validation over generated/real Lua bytes, then
retain the controller ACK/qualification lifecycle. Assigning PLAN_COUNT alone or
hand-building SweepEvidence is insufficient producer/consumer proof.

Add a small synthetic alternate-count test through real controller qualification
and producer/consumer plan expectations, with all existing identity/ACK barriers
still enforced. Avoid repeated target/catalog serialization in frame loops; cache
immutable packaged expectations once per process. Parent will re-run the full
default suite after integration; preserve its <180-second acceptance requirement.
