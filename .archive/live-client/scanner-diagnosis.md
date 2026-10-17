# Live scanner diagnosis

Date: 2026-10-14

This is a read-only diagnosis of the deployed Forever client (1.60.1.70374),
Crowley format 2, and the installed Auctionator 341 source. The two failed
SavedVariables scans were decoded in place and left unchanged. There are no
retained market prices in either scan.

## Persisted evidence

`WTF/Account/*/SavedVariables/Crowley.lua` contains two format-2 scans for
`beta-normal-alliance`, both using plan hash
`0712de248d42bd39d9a3991b74ece968b92f768e033af3a6116bdb7a93453a7c`.

| scan order | queried observations | reason counts | unqueried observations | rows | owned |
| --- | ---: | --- | ---: | ---: | --- |
| older | 20 | `query_timeout` 19, `sweep_timeout` 1 | 408 | 0 | unqueried / `not_started` |
| newer | 3 | `query_timeout` 2, `ah_closed` 1 | 425 | 0 | unqueried / `not_started` |

The payload decoder (`decode_json_payload`) successfully decomposes both raw
deflate/base64 payloads. Strict envelope validation then fails at
`observations.3825.rows/count mismatch`; this is a wire-shape error, separate
from the scanner's zero-result behavior.

## Confirmed wire defect: native JSON turns empty tables into arrays

`addon/Crowley/Scanner.lua:671-676` serializes the payload with the native
`C_EncodingUtil.SerializeJSON`. Observations use `rowMap` at lines 175-179 and
owned results use an auction-ID map at lines 516-524. When those maps are empty,
the native serializer writes `[]`, which is what the persisted payloads contain
for every zero-row observation and for `owned.rows`.

`src/crowley/core/scanformat.py:503-506` requires observation `rows` to be a
dict, and `:619-622` requires the same for owned rows. Thus a real client
payload with `rowCount == 0` is rejected during server validation. The test harness does
not expose this because `tests/wow_harness.py:454-472` converts an empty Lua
table to a Python dict before its JSON stub serializes it.

The documented `C_EncodingUtil.SerializeJSON(value, options)` API has only
`JSONSerializationOptions.ignoreSerializationErrors`; it has no option to force
an empty Lua table to encode as a JSON object. A producer-side “force object”
call would therefore be an unsupported assumption.

The approved plan now defines the actual native keyed-collection contract:
`[]` only for empty collections, objects only for nonempty collections, with
strict validation followed by normalization to internal Python dictionaries.
It rejects empty objects and nonempty arrays, preserves original payload bytes,
and needs no ingestion-consumer rewrite. Update Lua/Python wire tests and
fixtures together; do not add a compatibility decoder. Preserve these failed
scans as evidence. See the final round in `.archive/PLAN-live-client.md`.

## Confirmed native API parity and the response-contract gap

The basic call signatures are not the defect found here:

* `Scanner.lua:459` calls `GetItemKeyInfo(itemKey, false)`, matching the
  documented optional `restrictQualityToFilter` argument.
* `Scanner.lua:463-470` builds a one-element sort table and calls
  `SendSellSearchQuery` with an item key whose item level and suffix are zero.
  This matches Auctionator's `SaleItem.lua:390-417`; the installed constants
  use price sort `0` and buyout sort `4` at
  `Source_ModernAH/Constants/Main.lua:5-6`.
* The result fields Crowley reads (`unitPrice`, `buyoutAmount`, `quantity`,
  `auctionID`, owners, item link/key) match the fields consumed by Auctionator
  in `Source_ModernAH/Tabs/DataProviders/SearchProvider.lua:137-195` and
  `:229-253`.

There is, however, a concrete behavioral contract that Crowley does not carry
over from Auctionator. `Source_ModernAH/AH/Mixins/SearchScan.lua` documents at
lines 1-11 that native item-key searches can be ignored. Its result handler at
lines 36-64 checks `HasSearchResults`, `HasFullCommoditySearchResults` or
`HasFullItemSearchResults`, and the loaded quantity. It retries the same search
when results are absent or when a partial response has zero quantity. Its
`AttemptSearch` path at lines 88-103 waits for item-key metadata, registers the
result events, and only then invokes the raw native query.

Crowley instead binds events at `Scanner.lua:434-455`, including both
`*_SEARCH_RESULTS_ADDED` and `*_SEARCH_RESULTS_UPDATED`, requires both throttled
message barriers, and lets `collectResults` at `:383-420` consume the result
event without the `HasSearchResults`/quantity readiness check or the
Auctionator retry. The installed Auctionator registers only the two UPDATED
events in `SearchScan.lua:14-17`; the client API marks item RESULTS_ADDED as a
synchronous event, and has no corresponding commodity ADDED event in its
generated event list. Crowley can therefore consume an early/different event
than Auctionator. The live evidence is consistent with this gap: of 23 attempted
items, 21 ended with `query_timeout` and two were interrupted by sweep/AH closure
without a row. It does not prove whether Forever emitted an empty provisional
result or ordered `*_SEARCH_RESULTS_UPDATED` before one of the throttled
barriers, because the current payload records only the final reason.

The two concrete native-response hypotheses are therefore:

1. The client emitted a provisional/empty result event. Crowley immediately
   proceeded to paging or waited for a later event; Auctionator would retry the
   original query after checking `HasSearchResults` and quantity.
2. The client delivered the result event before
   `AUCTION_HOUSE_THROTTLED_MESSAGE_SENT` or
   `AUCTION_HOUSE_THROTTLED_MESSAGE_RESPONSE_RECEIVED`. Crowley's guard drops
   that event because `sentBarrier`/`responseBarrier` is false; Auctionator does
   not use those barriers for result readiness.

No current evidence supports changing result field names, sort values, item-key
shape, or the compression/base64 codec. A subsequent bounded implementation
round should capture per-query event ordering and the three readiness values so
these two hypotheses become distinguishable.

## Bounded implementation and test scope for parent review

1. Make the format-2 row collections canonical arrays end to end, covering the
   addon producer, strict validator, server ingestion, and fixtures. Add a real
   native-shaped zero-row observation and zero-row owned batch to the wire tests;
   retain full, bounded, incomplete, and owned rows tests with nonempty arrays.
2. Mirror Auctionator's minimal response gate/retry around one native search:
   metadata readiness, matching result event, `HasSearchResults`, full/partial
   state, and nonzero quantity before requesting more pages. Define one bounded
   retry/timeout result and preserve an explicit failure reason.
3. Extend the Lua harness with event-order cases (result before throttled
   barriers, empty provisional result followed by data, stale result, and a
   normal populated response). Verify that one populated response creates rows,
   that retries do not duplicate result IDs, and that the existing page/depth
   limits still hold. Add a server ingestion test for the canonical array form.

This diagnosis does not authorize or include those implementation changes. The
current production state remains: two persisted zero-row scans, no uploaded
market observations, and no acknowledgement proof.
