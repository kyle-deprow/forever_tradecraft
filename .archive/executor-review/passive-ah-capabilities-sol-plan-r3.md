# Sol plan review R3: passive AH capabilities

This was a bounded read-only review of the two R2 corrections. I did not run
tests, inspect the game, or exercise source, configuration, input, network,
runtime, or Git paths.

## Inputs checked

- `.archive/PLAN-passive-ah-capabilities.md` — SHA-256
  `d9c1db55c486cea4f5720a86270a41c3a948c6c871b11fe973f68e1196ef3e38`
- R2 review — SHA-256
  `74d08ed9165aece956f50e8d98c99c94f6c7ec0e6a25820e7668f7f175fb9e77`
- `.archive/PLAN-deterministic-ah-interaction.md` — SHA-256
  `6749abe7dff023202b98877409c28e99f3b54908ea992beec5bdd9278e610a47`

## R2 closure

- **Range and interactability are now one exact bounded contract.**
  `.archive/PLAN-passive-ah-capabilities.md:83-87,94-99,113-120,153-156`
  permits one protected `UnitIsInteractable("target")` call. Its boolean supplies
  `interactable`; it supplies an equal `range` and the fixed accessor literal
  only after reviewed source proves the required auctioneer-range semantics.
  Otherwise both range fields remain `contract_unverified`. Indexed predicates
  and encoded accessor/index strings are excluded from schema 1 and require a
  later protocol revision.
- **Binding observation is separated from input qualification.**
  `.archive/PLAN-passive-ah-capabilities.md:129-144` retains the exact nonempty
  bounded one-return string as private diagnostic evidence but does not call it
  supported or authorize a key. Fact 1 remains incomplete until a later
  reviewed driver plan accepts that exact value in a finite allowlist and seals
  its measured XKB/keycode mapping. Nil primary uses the exact known-absent
  `OptionalFact` without a reason; duplicate/extra returns disqualify the
  observation.

The plan is therefore implementable as a passive diagnostic publisher and
strict decoder migration. It does not yet establish a five-fact qualification:
the build-pinned API/GUID/range/UI table, actual CVar and target results,
ordered live frame bundle, and later binding allowlist/XKB seal remain explicit
gates at `.archive/PLAN-passive-ah-capabilities.md:128-167,169-186,202-207`.
Unknown or unreviewed facts remain ineligible. This review approves no AH input,
driver implementation, model-call removal, or Rust work.

## Must-Fix

None.

## Should-Fix

None.

## Nits

None.

STATUS: READY
