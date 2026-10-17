# Sol plan review R2: passive AH capabilities

This was a bounded read-only closure review. I did not run tests, inspect the
game, or exercise configuration, input, network, Git, or runtime paths.

## Inputs checked

- `.archive/PLAN-passive-ah-capabilities.md` — SHA-256
  `04a313458aa3e8c2624662cb1df49127ce170ffa39789bbdf2f46a1b8d4b11b9`
- R1 review — SHA-256
  `e473ec0e62a865f992685f754205ccc39d1863f866a55dad5da6919eeb9bddad`
- `.archive/PLAN-deterministic-ah-interaction.md` — SHA-256
  `6749abe7dff023202b98877409c28e99f3b54908ea992beec5bdd9278e610a47`

## R1 closure

- **Privacy/ownership is closed** at
  `.archive/PLAN-passive-ah-capabilities.md:7-31,157-174`. No interaction
  identity enters `CrowleyDB.probe`; the unchanged companion path is covered by
  a privacy regression, and qualification uses bounded private decoded frames.
- **Wire shape and rollout are closed in principle** at
  `.archive/PLAN-passive-ah-capabilities.md:33-121,176-188`. The plan states the
  one-way decoder-first cutover, exact union variants and key sets, bounds,
  known absence, cross-field validation, payload proof, and ownership of the
  direct protocol tests in `tests/test_session.py`.
- **Valid absence and failures are separated** at
  `.archive/PLAN-passive-ah-capabilities.md:53-72,101-115`. Nil is no longer
  globally treated as failure, and missing/throw/type errors cannot become
  false evidence.
- **Ordered event/reload proof is closed** at
  `.archive/PLAN-passive-ah-capabilities.md:157-188`. Same-boot target/show/close
  deltas and different-boot reload evidence require retained ordered strict
  frames; a single overwritten receipt cannot qualify them.

The plan also correctly leaves the actual build facts deferred. There is no
current five-fact qualification until reviewed source pins the CVar accessor,
GUID grammar, range semantics, overlay path and popup IDs, and a live ordered
bundle proves the binding/value/target/range/UI results. Lines 125-155 fail
closed on every missing row rather than treating broad unknowns as acceptance.

## Must-Fix

1. **The exact schema cannot represent one of the range sources the plan says
   may qualify, and it never assigns a source to `target.interactable`.**

   - File: `.archive/PLAN-passive-ah-capabilities.md:83-87,94-99,113-115,142-155`
   - The wire carries only `rangeAccessor: Fact<string>`. Lines 142-144 also
     permit a separately reviewed `CheckInteractDistance`-style accessor/index,
     but no field carries that index or the arguments whose semantics were
     reviewed. Encoding an index into the accessor string would invent an
     unstated grammar. Separately, the schema contains both `interactable` and
     `range`, while the API table describes only the predicate selected for
     range; it does not state which exact call supplies `interactable`, whether
     one protected call may supply both values, or the equality rule if it
     does. Two implementations can therefore emit different evidence under the
     same strict schema.
   - Correction: choose one bounded contract. Prefer restricting this slice to
     source-proven `UnitIsInteractable("target")`; define exactly whether it
     supplies `interactable`, `range`, or both, including call count and any
     equality invariant, and leave fact 4 `contract_unverified` if its range
     meaning is not proven. If an indexed predicate remains allowed, replace
     `rangeAccessor` with a closed source union that carries the literal
     accessor and exact unit/index arguments. No index may be added after
     qualification without a protocol revision.

2. **Fact 1 still has no exact qualification rule for a supported unmodified
   keyboard binding, and its nil encoding is internally contradictory.**

   - File: `.archive/PLAN-passive-ah-capabilities.md:53-72,77-81,101-104,129-133,190-193`;
     `.archive/PLAN-deterministic-ah-interaction.md:56-59,170-175`
   - The schema bounds a binding as an arbitrary nonempty string of at most 96
     UTF-8 bytes, while the parent plan requires a supported unmodified
     keyboard value and rejects chords, mouse inputs, and values outside a
     predeclared driver allowlist. “One valid keyboard return” therefore has no
     testable meaning for declaring the five-fact bundle complete. In addition,
     line 131 calls nil primary both known absent and `unbound`, but exact known
     absence has no `reason` key; `unbound` belongs only to unknown/error.
   - Correction: keep the raw observed value local but define the exact
     producer grammar and the separate qualification predicate. Either pin the
     small accepted unmodified binding allowlist in this plan, or state that
     this slice proves only the observed one-return fact and that fact 1 remains
     incomplete until the later reviewed driver plan accepts and seals that
     exact value. Encode documented nil as the exact known-absent
     `OptionalFact` and remove `unbound` from that branch, or change the branch
     to an unknown union consistently.

## Should-Fix

None.

## Nits

None.

STATUS: NEEDS WORK
