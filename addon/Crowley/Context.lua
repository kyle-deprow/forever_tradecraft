local _, ns = ...

local Context = {}
ns.Context = Context

-- Goblin-run houses shared by both factions (15% cut), matched against zone and subzone text.
local NEUTRAL_ZONES = {
  ["Booty Bay"] = true,
  ["Gadgetzan"] = true,
  ["Everlook"] = true,
}

Context.VALID = {
  region = { us = true, eu = true, kr = true, tw = true, cn = true, beta = true },
  ruleset = { normal = true, pvp = true, rp = true, hardcore = true },
  faction = { alliance = true, horde = true, neutral = true },
}

local REGION_BY_ID = {
  [1] = "us",
  [2] = "kr",
  [3] = "eu",
  [4] = "tw",
  [5] = "cn",
  [110] = "beta",
}

local RULESET_BY_REALM = {
  Normal = "normal",
  PvP = "pvp",
  RP = "rp",
  Hardcore = "hardcore",
}

local BETA_REALM = "Classic Beta PvE 2"

local function validate(field, value, source)
  if value == nil or not Context.VALID[field][value] then
    error(("invalid %s %s %q"):format(source, field, tostring(value)))
  end
  return value
end

local DETECT = {
  region = function()
    local id = GetCurrentRegion()
    local region = REGION_BY_ID[id]
    if not region then error(("unknown native region id %s"):format(tostring(id))) end
    return region
  end,
  -- Forever is realmless; launch realm names identify the ruleset exactly. The
  -- verified beta realm is kept separate until other beta realms are identified.
  ruleset = function(region)
    local realm = GetRealmName()
    if region == "beta" then
      if realm ~= BETA_REALM then
        error(("unknown beta realm %q"):format(tostring(realm)))
      end
      return "normal"
    end
    local ruleset = RULESET_BY_REALM[realm]
    if not ruleset then error(("unknown native realm %q"):format(tostring(realm))) end
    return ruleset
  end,
  faction = function()
    if NEUTRAL_ZONES[GetZoneText()] or NEUTRAL_ZONES[GetSubZoneText()] then return "neutral" end
    local faction = UnitFactionGroup("player")
    if not faction then error("unable to detect native faction") end
    return faction:lower()
  end,
}

-- The house a scan made right now belongs to. `/crowley set` overrides win over detection;
-- `source` records which fields were overridden so attribution can be audited.
function Context.House()
  local settings = ns.db.settings
  local house = {}
  local overridden = {}

  -- Validate persisted overrides before consulting any native value. An invalid
  -- setting must never be silently treated as auto detection.
  for _, field in ipairs({ "region", "ruleset", "faction" }) do
    local setting = settings[field]
    if setting ~= nil then validate(field, setting, "saved override") end
  end

  for _, field in ipairs({ "region", "ruleset", "faction" }) do
    local setting = settings[field]
    if setting ~= nil then
      house[field] = setting
      overridden[#overridden + 1] = field
    else
      house[field] = field == "ruleset" and DETECT[field](house.region) or DETECT[field]()
    end
    validate(field, house[field], "detected house")
  end
  house.key = ("%s-%s-%s"):format(house.region, house.ruleset, house.faction)
  house.source = #overridden > 0 and ("override: " .. table.concat(overridden, ",")) or "auto"
  return house
end

-- Raw client facts stored with every scan, so attribution can be re-derived server side.
function Context.Snapshot()
  local playerFaction = UnitFactionGroup("player")
  if type(playerFaction) ~= "string" or playerFaction == "" then
    error("native player faction must be a non-empty string")
  end
  local version, build, _, interface = GetBuildInfo()
  return {
    character = UnitName("player"),
    realm = GetRealmName(),
    playerFaction = playerFaction,
    zone = GetZoneText(),
    subzone = GetSubZoneText(),
    locale = GetLocale(),
    clientVersion = version,
    clientBuild = build,
    interface = interface,
    addonVersion = ns.VERSION,
  }
end
