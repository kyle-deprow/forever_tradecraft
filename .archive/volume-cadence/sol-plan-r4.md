Must-Fix

- None.

Should-Fix

- None.

Nits

- None.

Revision 4 is coherent with the existing format-2 contract:

- Owned collection states now distinguish “never entered” from an interrupted active owned query, and `house_changed` is legal in the owned reason enum.
- Incomplete observations may retain bounded captured evidence without claiming a proved prefix or becoming movement-eligible.
- Unsafe rational comparisons correctly force `numeric_range` while preserving individually safe rows in ordinal order.
- Numeric row ordinals remove dependence on JSON object iteration order; unrestricted equal-price tie ordering does not weaken price-prefix proof.
- Full/bounded scopes retain strict pairwise comparison safety, exact ordering, and bounded-depth/witness requirements.

STATUS: READY
