Must-Fix

1. **Grouped rows can still create false individual disappearances.**
   Lines 60–65 and 257–263 exclude grouped rows themselves, but do not handle grouping changing between observations. A previously individual auction may be absorbed into a grouped current row; its ID then appears missing even though the auction may still be present.

   Concrete fix: individual inference for a variant/price stratum is eligible only when neither observation contains a grouped or unknown row capable of concealing the compared IDs. Exclude both removals and additions for affected strata. Add tests for individual→grouped and grouped→individual transitions with unchanged supply.

2. **“Exact” Lua rational comparison lacks a safe numeric domain.**
   Lines 135–141 require exact rational ordering in Lua, but Lua 5.1 numbers are IEEE-754 doubles. Cross multiplication can lose integer precision, making level ordering and cutoff selection inexact even though Python later uses exact arithmetic.

   Concrete fix: define and validate a safe-integer range for IDs, money, quantities, and rational components. Reduce fractions before comparison and check `numerator <= floor(MAX_SAFE_INTEGER / other_denominator)` before cross multiplication. Unsafe values must make the observation incomplete with a stable `numeric_range` reason rather than be rounded. Apply equivalent validation server-side and add boundary tests.

Should-Fix

1. **Clarify the API identity for raw item-key variants.**
   Lines 145–149 preserve raw level/pet fields in addition to the canonical string, and line 249 requires raw-key matching, but `/items/{item_key}/volume` identifies only the string key. Specify that the response returns separate raw-variant series, or extend the canonical path key so raw item level and pet species cannot be aggregated accidentally.

2. **Name the normalization policy used at line 250.**
   No `normalizationPolicy` field exists in the exact plan or payload schema. State explicitly that format 2 itself is the immutable `whole-buyout/quantity reduced-rational` policy and any semantic change requires format 3, or add a hashed policy identifier to the plan body.

3. **Define the conflict digest as the whole logical scan.**
   Lines 183–192 say “canonical parsed payload content,” which could mean only the compressed inner payload. The digest must cover every validated envelope field plus the decoded payload, excluding only transport encoding/compression differences. Otherwise the same UID with changed house or timestamps could be accepted as a duplicate.

4. **Document the acknowledgement round trip precisely.**
   At capacity, one `/reload` writes scans for the companion, but acknowledgements written afterward into Data.lua are not loaded until another login/reload. Lines 231–236 should state this two-boundary behavior so “flush/reload” does not imply immediate resume.

Nits

- Line 33 should say “successful zero eligible buyout supply”; bid-only auctions may still exist under line 162.
- Enforce that a bounded noncommodity observation must have `sourceComplete=true`; only commodities may stop early after proving a higher-price witness.
- Record the assumption that `OwnedAuctionInfo.buyoutAmount` is whole-auction copper for both item kinds, since the generated structure names the field but does not document that semantic.
- Lines 8–9 say the starting item rotates, while lines 207–211 leave the start unchanged after a fully completed wrap. Either advance one item after complete sweeps or narrow the claim to rotation after capped/partial sweeps.

STATUS: NEEDS WORK
