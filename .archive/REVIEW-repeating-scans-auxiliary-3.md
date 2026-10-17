# Auxiliary review round 3

Sol verdict: MAJOR ISSUES, with two remaining must-fix defects. The parent
reproduced 100 addon passes after round 2. The armed-fence phase, exact decoded
plan IDs/metadata, finite heap and UTF-8 boundary corrections were confirmed.

1. Require the exact canonical planJSON bytes, not just equivalent decoded data.
   A pretty-printed canonical body with the unchanged canonical hash currently
   starts a scan that the server rejects as noncanonical. Compare against one
   exact canonical reconstruction, including escaping/key ordering, before any
   scan/schedule; no hash API guesses or compatibility encodings. Test both
   whitespace and equivalent alternate JSON representation, and bind tests to
   the actual shipped catalog JSON/hash. Keep the same auxiliary file fence.
2. Parse the pinned Codex CLI event protocol, not Responses API event shapes.
   Remove response.created/response.completed/item.error compatibility records.
   Enforce exact lifecycle record shapes and nonempty item IDs. Support valid
   completed reasoning records while extracting exactly one structured final
   agent message. Reject unknown/tool payloads at every lifecycle stage, extra
   fields, duplicate answers, incomplete or invalid ordering and failure events.
   Keep only the exact already-verified benign diagnostic exception.

Official [noninteractive documentation](https://learn.chatgpt.com/docs/non-interactive-mode)
confirms thread/turn/item/error event families, item IDs, reasoning items and
JSONL output. Preserve installed codex-cli 0.162.1 and gpt-6-luna/low; verify
version-specific shapes against the installed implementation and existing actual
trace or a bounded tools-disabled neutral CLI smoke if needed. Do not infer CLI
records from API Responses events or accept invented compatibility shapes.

Add a production frame decode assertion for the armed-fence regression, not only
Agent.Publish return inspection. Main-owned model fixtures must become complete
ID-bearing pinned streams; coordinate required builder/schema changes directly
with the main engine owner rather than allowing ID-less production items.

Full addon and relevant parser/CLI checks, strict warnings, Ruff/format, parent
reproduction and Sol re-review remain required. Same ten-file auxiliary scope;
no edits to main/native files. No GUI, service activation, production data/auth
changes, secrets, git mutations or fake live evidence. Report the whole outcome.
