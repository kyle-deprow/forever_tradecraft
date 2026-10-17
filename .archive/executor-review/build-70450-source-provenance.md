# Community UI source 70450 provenance

Read-only Luna research, 2026-10-16. Current forever branch commit
172a387e3ab85b26e6640d3058d5ec1e6ccd4c63 is titled 1.60.1 (70450),
committed 2026-10-16T22:31:27Z. Prior pinned 70425 commit is
b401e0332adfbf0460d319b06d8ea29279a941f1.

[Commit](https://github.com/Gethe/wow-ui-source/commit/172a387e3ab85b26e6640d3058d5ec1e6ccd4c63)
[Comparison](https://github.com/Gethe/wow-ui-source/compare/b401e0332adfbf0460d319b06d8ea29279a941f1...172a387e3ab85b26e6640d3058d5ec1e6ccd4c63)

The comparison reports one new commit and only version.txt changed, from
1.60.1.70425 to 1.60.1.70450. The relevant generated API declarations and
Controls.lua are byte-identical across the snapshots:
- UnitDocumentation.lua: a823e84f90fabe58d9ffe547ea17eae83708d451e593b4052bce002cc02ce5c1
- CVarDocumentation.lua: 7e99fe35756236ecf6d723ff755edaefd7c41007ef53f58d48e2d2f6899296b1
- AuctionHouseDocumentation.lua: d970632b8175ef98c07cd7876debdef2a29ca023a32063787f7796795cea2372
- Controls.lua: 4664ccfcfd4e213ed5234a4f79a111c3faad94ee9dabb92c8fa42e4ffd886cf9

Paths are Interface/AddOns/Blizzard_APIDocumentationGenerated/ for generated
documents, and Interface/AddOns/Blizzard_SettingsDefinitions_Frame/Controls.lua.
IsMounted is not declared in UnitDocumentation; installed-client probes supply
its evidence. GetUnitSpeed declares ordered current/run/flight/swim numeric
returns without establishing world units or a universal ceiling. CTM maps
CLICK_TO_MOVE to autointeract; GetCVarBool is nilable boolean. Search/result,
more-results, commodity/item key and throttle event declarations are unchanged.

This is community-mirrored client source, not official Blizzard provenance,
installed CASC verification, or proof of runtime parity. Preserve build gates
until fresh native qualification. Existing 70450 stationary motion probes are
recorded separately; representative live scanner query/result/throttle evidence
still remains to be collected. No source/runtime/game mutation was performed
by this research worker.
