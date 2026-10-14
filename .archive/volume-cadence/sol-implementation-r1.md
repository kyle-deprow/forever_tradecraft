Must-Fix

1. addon/Crowley/Scanner.lua:319-347,355-368;tests/wow_harness.py:88-156 — Wrong Forever API. SendSellSearchQuery exactly(itemKey,sorts,separateOwnerItems), not page,false. Commodity getters/events numericitemID; metadata numericitemID; ItemKeystructure must compare fields. Pagination HasFull*/RequestMore*, ADDED events; no nonexistent itemRECEIVED event/count50 completeness. Harness must match documentedAPI; fresh-sendbarrier and stale/unrelated/no-payload tests, tenpagecaps.
2. Scanner.lua:52-140,276-302;harness116-156 — Wrong documented rowfields. Items itemKey/owners/timeLeft; owneditemID fromitemKey. Parse documentedstructures; bonuses fromlink; preserve commoditygrouping. Exact rowshape roundtrips.
3. Scanner.lua:217-252 — Boundedcutoff/witness missingkindtags; usesrow20/21 notdistinctlevels. Useplan.initialPriceLevels, closedsharedpriceboundary, propertaggedwitness; manyequalrows+20higherlevelregression.
4. Scanner.lua:180-215,319-329,401-424;scanformat359-370 — Throttleditemretry compares sweepstate toitemstate so neverretries. Pagecap doesn'tclear/advance. Globalsweep timeout mislabelsactiveunqueried/discardsrows. Tailabortreasons conflictvalidator. Token-safe callbacks, preservepartial, advancecaps; actualLua logout/close/house/metadata/paging/sweeptimeout validation.428itemtest currentlytimesout ratherthanprovingallsends.
5. scanformat330-469 — Enforce successfulscope retainedlevels/reasons/order/pairwisecomparison-safety usingplaninitialPriceLevels. Full>depthreject; bounded arbitrarylevels/errorreasonsreject; exactnumericboundary tests.
6. ingest223-247;app204-214,234-269;migration33-52 — market_observations.item_keystoresbasequeryID, variantpaths inaccessible/mixed. Preservequeryscope andproject/indexcanonicalvariants; variant-filter volume/history while retainingfailed/unqueriedgaps. Level/petvariant DBregressions.
7. volume207-265,281-315 — Groupedscopesvalid+zerorate wrong; excludeindividualdenominator andnullunknown. Aggregatecommoditydepletion/replenish andallindividual/expiry/counts atreporttop. Allgrouped/mixedgrouped/commoditymultiinterval tests.

Should-Fix

1. volume40-49,287-294;app231-243 — SortsquerynotSWEEPstart;latestoutsidewindowmissing. Sweepstart+ordinalorder; end-windowintervalfilter; latestindependent.
2. ingest93-149;app244-279 — Ownedquerywindow/timeincorrectuseswholesweep; inconsistentunitscountedconfirmed. Actualownedbounds/time; inconsistentseparate.
3. ingest31-32,168-178;app81-83 — LegacyUIDcollision422should409; unstorableepochs500afterarchive. Prearchive422timestampsvalidation, allUIDconflicts409.
4. Scanner157-163;Commands11-26 — Missingcursorreset/continuationplanlogandhash; statusmissingplan/counts/reloadguidance.

Nits: none. Scopedchangeswithin authorizedset.
STATUS: MAJOR ISSUES
