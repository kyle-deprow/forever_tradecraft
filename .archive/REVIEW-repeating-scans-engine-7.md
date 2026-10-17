# Engine review round 7

Sol verdict: MAJOR ISSUES. Prior green tests do not establish the production
contracts below. Same eleven-file main ownership; native six-file owner is
implementing REVIEW-repeating-scans-native-8.md concurrently. Coordinate interfaces
directly and finish both actual producers and consumers.

## Must fix

1. Complete the real native integration: durable before-reset journal records
   and the native owner's verified archive receipt; publish operator-visible
   hold-required/measure-ready/resume-ready and failure/restoration state through
   existing status/IPC. Bind all exact callbacks, support resume stage, return
   actual decoded phase/ordinal, enforce requested stages, and prove fresh resumed
   normal/0. Archive both complete NativeMemoryMeasurement records, not a subset.
   Current identity-only callbacks and omitted measurement records are insufficient.
2. Treat uncertainty conservatively BEFORE physical dispatch. A crash/pause/stop
   after input but before a dispatched checkpoint must not lose the effect.
   Both slash commands and named actions need the same durable no-replay rule;
   an intent stored as pending cannot simply be assumed safe/pre-dispatch.
3. Implement honest intent-specific restart reconciliation for scan, open_ah,
   bounded login recovery actions, pre_logout_fence, save/upload/ack and logout.
   Never invent ready/world when fields are omitted. Generic UID absence cannot
   resolve unrelated intent. Recognize ready AND scheduled as idle. A completed
   logout at character select must be recognized with read-only visual and disk
   evidence before any automatic login attempt; no relog just to discover it.
   Fresh gates are required before input, not before read-only terminal recovery.
4. Require the exact loaded UID in acknowledgement completion and bind saved,
   companion-uploaded, published Data ack, loaded witness and qualified evidence
   to one UID. Recovered acknowledgements must reconstruct and qualify full
   format-2 evidence/timestamps/boot/sequence, or explicitly reject an unprovable
   cycle; never silently jump to REOPEN and skip qualification. Remove obsolete
   acknowledged()/ack_reload_sent() alternate lifecycle routes and update callers.
5. Make outcome archival AND resulting controller counters/state one recoverable
   durable transaction. Fresh startup must replay pending committed outcomes and
   repair all derived artifacts/checkpoints exactly once. Reject conflicting
   payloads under the same outcome ID. Remove preliminary acknowledgement artifacts
   that shadow the later complete record. A manifest replayed only when an old
   in-memory caller retries is insufficient. Compute the complete outcome and
   resulting state before commit; ensure crash boundaries cannot lose accepted
   counts, duplicate counts, skip qualification, or leave partial proof forever.
6. An already armed fence after restart still requires a new exact fence command
   and a newer same-boot acknowledgement. Missing process-local observation must
   trigger fresh proof rather than wait forever or allow unproven logout.
7. Validate nativePhase type before set membership. All malformed input,
   including lists/dicts, raises ProtocolError rather than raw TypeError.
8. Replace tests/test_session.py's synthetic range(1,429) addon plan with the
   actual set_canonical_plan() fixture. Keep strict canonical validation intact.

## Verification and completion

Create production-path regressions that fail for each concrete case above before
claiming a fix: injected pause/stop/crash at the dispatch/journal gap; each intent
with fresh owner; real character-select terminal path; exact loaded UID and
recovered qualification; failure at EVERY manifest/artifact/checkpoint publication
with a fresh owner retry; armed fence restart; malformed phase; full actual native
callback/status handshake and durable archive receipt ordering. Do not just call
private transitions to simulate success or reuse process-local proof on restart.

Use only existing owned files: six main modules, four main test files and
docs/REPEATING_SCANS.md. The independent regression owner retains its files.
Run all owned tests with strict thread/unraisable/fork warning errors, scoped Ruff
and format, then parent combined suite and read-only Sol review. Update docs to
describe the executable operator handshake and its actual status fields. No GUI,
game input, live proc reset, service activation, SavedVariables/Data edits, prodDB,
git operations or unrelated files. DONE only after the complete batch is proven.
