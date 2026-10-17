# Sol plan review R1: passive AH capabilities

This was a bounded read-only review. I did not run tests, inspect the live game,
change configuration, or exercise any input, network, scan, or runtime path.
Implementation remains sequenced after the in-progress 16-by-8 runtime batch so
that its accepted protocol/source binding is not invalidated.

## Inputs checked

- `.archive/PLAN-passive-ah-capabilities.md` — SHA-256
  `b0082c1cad36819f9e7a6acdd09e48082ca6d4e17415a0d1d3ff45a8c9e4b0b9`
- `.archive/PLAN-deterministic-ah-interaction.md` — SHA-256
  `6749abe7dff023202b98877409c28e99f3b54908ea992beec5bdd9278e610a47`
- `.archive/PLAN-native-semantic-observations.md` — SHA-256
  `15d9ad403bde2ed851fcf49a5ccc38c6136505e689b9f8109402bbf9949ea9a7`
- `addon/Crowley/Agent.lua` — SHA-256
  `3f7356118ba2804c9224663262ad851468a643b88f628139a95fa20bbc07a65d`
- `addon/Crowley/Probe.lua` — SHA-256
  `dbd7afb6697a908a63257d69c4b34dcb04ef358898c558d398000611e1fc589d`
- `src/crowley/session/protocol.py` — SHA-256
  `cf13dedd7a37e553ac799b87dd5429cc29b5910483661f994ffdec3b38a74d2f`
- `tests/wow_harness.py`, `tests/test_addon.py`, and
  `tests/test_session_runtime.py` — SHA-256 respectively
  `7228357e7a1f24703195169db3879f0d64da8d8a0e16a56787786e4c8f3037d9`,
  `f3fe07faaba496437c67289b5f2f711ad3f716f26ceb435c1f1a9b1f8de14583`, and
  `9d634f603968e85c253dfc4116102deedb09fc18e2ed6b5542c3c1b0d2d64868`.

The passive producer is feasible in `Agent.lua`: it can use the existing
`ns.On` dispatcher, read the APIs without touching `Scanner.Status`, and add no
query, binding, CVar, target, or UI mutation. The following contract gaps block
implementation and qualification as written.

## Must-Fix

1. **The proposed probe receipt is not private on the actual companion path.**

   - Files: `.archive/PLAN-passive-ah-capabilities.md:10-20,95-113`;
     `addon/Crowley/Probe.lua:39-85`;
     `src/crowley/companion/sync.py:93-108`;
     `src/crowley/server/app.py:129-135`
   - The plan places the exact interaction object, including target name/GUID
     and binding facts, under `CrowleyDB.probe` and calls that receipt private.
     The existing companion posts that entire object to `/v1/probes`, and the
     server stores it without field filtering. A normal `/reload` therefore
     sends the proposed identity receipt to the server. This also contradicts
     the instruction to keep raw receipt/build detail private.
   - Correction: persist a separately named, bounded local receipt that the
     companion does not upload, with a strict envelope binding capture time,
     build/interface/addon version, Agent boot, and the nested interaction
     schema. Keep `CrowleyDB.probe` free of interaction identity. Add
     `tests/test_companion.py` to the test fence and prove that a SavedVariables
     file containing the local receipt produces a `/v1/probes` body without
     that receipt, GUID, name, or binding. If the design instead redacts in the
     companion, add the companion and its tests to production ownership
     explicitly.

2. **The stated strict wire contract is still descriptive, and schema-3
   compatibility is only one-way.**

   - Files: `.archive/PLAN-passive-ah-capabilities.md:30-62,95-103`;
     `src/crowley/session/protocol.py:229-285`;
     `tests/test_session.py:526-553`
   - `protocol.py` currently requires the exact schema-3 root key set. The old
     decoder rejects a new `interaction` key, even though a new decoder can be
     taught to accept legacy frames. The plan does not choose a decoder-first
     cutover or a new schema, and it does not give exact nested key sets,
     variant-specific key sets, value types, string/array/count limits, epoch
     bounds, popup representation, or cross-field rules. Phrases such as
     "facts (or references)" cannot be implemented as a closed schema. The
     missing limits also make the claimed worst-case 2,000-byte proof
     undefined.
   - Correction: write the complete JSON contract into the plan before coding.
     Define exact keys for every object and tagged-union variant, fixed
     accessor/action/unit literals, per-value enums and bounds, boot-scoped
     unsigned epoch behavior, string character/length rules, maximum popup
     count, and all known/unknown/error invariants. State whether preconditions
     are serialized values or are read from named existing root fields. Choose
     either (a) an explicit decoder-first stopped-owner cutover in which the
     extended schema-3 producer is never exposed to the old exact decoder, or
     (b) a new snapshot schema and the resulting consumer scope. Add
     `tests/test_session.py`, where the direct strict protocol tests actually
     live, to the owned test files. The payload test must construct the exact
     maximum legal complete snapshot through the real Lua publisher and Python
     decoder; successful publication, rather than a runtime telemetry outage,
     is the acceptance condition.

3. **The API-to-fact rules do not yet distinguish valid absence from failed
   evidence, and three build contracts remain unnamed.**

   - Files: `.archive/PLAN-passive-ah-capabilities.md:37-73,75-93`;
     `tests/wow_harness.py:81-97`;
     `.archive/PLAN-deterministic-ah-interaction.md:56-75`
   - A generic `nil_result` rule cannot qualify the intended observations.
     With one binding, absence of a second `GetBindingKey` return is the proof
     of exactly one binding; `StaticPopup_Visible(name) == nil` is normally the
     proof that that named popup is absent; and a nil load-on-demand
     `AuctionHouseFrame` can be a known unloaded state. Treating each as an
     unknown blocks the release gate. Conversely, treating every nil as known
     absence can hide an API/shape failure. The plan also leaves the GUID
     grammar, range semantics, overlay member path, and fixed popup names to an
     unspecified later acceptance, so a runtime result alone cannot truthfully
     turn `contract_unverified` into known.
   - Correction: add a build-pinned API table naming each exact accessor,
     arguments, return arity/types, documented nil/false meaning, exception
     handling, and source evidence. Enumerate the popup names and exact dialog
     overlay path. Capture the single `GetBindingKey` call with a Lua-5.1-safe
     vararg pack/count so a one-return result is known and any additional
     return is retained and refused. Pin an independently reviewed GUID grammar
     and range contract; if either cannot be established, keep that field
     `contract_unverified` and state that this passive slice cannot satisfy all
     five facts. Do not load the AH addon or substitute another accessor merely
     to convert an unknown into a value.

4. **One current overwritten receipt cannot prove the required event and reload
   transitions.**

   - Files: `.archive/PLAN-passive-ah-capabilities.md:50-53,75-90,105-126`;
     `addon/Crowley/Probe.lua:80`; `addon/Crowley/Agent.lua:269-310`
   - The gate requires `PLAYER_TARGET_CHANGED` and valid AH show/close epoch
     behavior, while the proof section also requires a new boot and fresh
     sequence after reload. `CrowleyDB.probe` retains only the latest record,
     and the proposed nested object has no boot or sequence. A positive counter
     in one receipt cannot show which event advanced it or establish same-boot
     ordering.
   - Correction: define the qualification artifact as a bounded ordered bundle
     of strict status frames plus the private receipt envelope. Require
     same-boot, strictly increasing sequence/time and the exact expected epoch
     delta across a passively observed target change and AH show/close
     lifecycle; after reload require a different boot and a newly sampled
     receipt/frame rather than comparing epochs across boots. No interaction
     action is released to manufacture these transitions: if ordinary
     sole-operator activity does not yield the complete bundle, the relevant
     fact remains unknown and deterministic AH interaction stays blocked.

## Should-Fix

None.

## Nits

None.

STATUS: NEEDS WORK
