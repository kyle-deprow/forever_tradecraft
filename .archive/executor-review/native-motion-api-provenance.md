# Native motion API evidence (70425)

Observed installed client after normal cached launcher recovery: WoW1.60.1(70425),
Arthur stationary in Ironforge, AHclosed. Original private screenshots remain
under ~/.local/state/crowley/executor-evidence/native-api-command-*-result.png.
Exact pcall C_CVar.GetCVarBool("autointeract") returned true,boolean,false.
GetUnitSpeed("player") returned0,7,7,4.7222218513489; GetFramerate71.153266906738.
All six IsFlying/IsFalling/IsSwimming/IsSubmerged/IsMounted/UnitOnTaxi globals
are functions; every actual return was boolean false in the final local print. No motion/camera/CTM
setting changes were used to obtain these facts.

Luna pinned Gethe community UI-source mirror revision
b401e0332adfbf0460d319b06d8ea29279a941f1, commit title1.60.1(70425),
2026-10-16T00:52:28Z. This is matching community source provenance, not an
independently verified official Blizzard or installed CASC source digest.

- [UnitDocumentation.lua](https://raw.githubusercontent.com/Gethe/wow-ui-source/b401e0332adfbf0460d319b06d8ea29279a941f1/Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua): GetUnitSpeed returns currentSpeed,runSpeed,flightSpeed,swimSpeed, all numeric. No unit/upper-bound contract is supplied by these generated declarations. Candidate state predicates are individually documented; no composite ground predicate is established.
- [CVarDocumentation.lua](https://raw.githubusercontent.com/Gethe/wow-ui-source/b401e0332adfbf0460d319b06d8ea29279a941f1/Interface/AddOns/Blizzard_APIDocumentationGenerated/CVarDocumentation.lua): GetCVarBool returns a nilable boolean.
- [Controls.lua](https://raw.githubusercontent.com/Gethe/wow-ui-source/b401e0332adfbf0460d319b06d8ea29279a941f1/Interface/AddOns/Blizzard_SettingsDefinitions_Frame/Controls.lua): autointeract is registered as Click-to-Move.

Consequences: observed speeds map to current0/run7/flight7/swim4.7222218513489.
Do not treat7 as universal speed ceiling or as position units without measured
correlation. Camera needs a fresh exact successful booleanfalse CTM sample;
true/nil/error/unsupported is not disabled. Model ground_clear describes visual
corridor evidence and cannot substitute for native movement-state facts. A strict
producer→protocol→decoder/MotionFrame→admission amendment is needed; preserve
CRS1 capacity, existing timing/resource limits and shared2-unit travel ledger.
