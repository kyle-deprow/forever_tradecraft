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
  region = { us = true, eu = true, kr = true, tw = true, cn = true },
  ruleset = { normal = true, pvp = true, rp = true, hardcore = true },
  faction = { alliance = true, horde = true, neutral = true },
}

local DETECT = {
  region = function() return GetCurrentRegionName():lower() end,
  -- Forever is realmless; the realm name the client reports is the ruleset (e.g. "PvP").
  ruleset = function() return (GetRealmName():lower():gsub("[^%a]", "")) end,
  faction = function()
    if NEUTRAL_ZONES[GetZoneText()] or NEUTRAL_ZONES[GetSubZoneText()] then return "neutral" end
    return UnitFactionGroup("player"):lower()
  end,
}

-- The house a scan made right now belongs to. `/crowley set` overrides win over detection;
-- `source` records which fields were overridden so attribution can be audited.
function Context.House()
  local house = {}
  local overridden = {}
  for _, field in ipairs({ "region", "ruleset", "faction" }) do
    if ns.db.settings[field] then
      house[field] = ns.db.settings[field]
      overridden[#overridden + 1] = field
    else
      house[field] = DETECT[field]()
    end
  end
  house.key = ("%s-%s-%s"):format(house.region, house.ruleset, house.faction)
  house.source = #overridden > 0 and ("override: " .. table.concat(overridden, ",")) or "auto"
  return house
end

-- Raw client facts stored with every scan, so attribution can be re-derived server side.
function Context.Snapshot()
  local version, build, _, interface = GetBuildInfo()
  return {
    character = UnitName("player"),
    realm = GetRealmName(),
    playerFaction = UnitFactionGroup("player"),
    zone = GetZoneText(),
    subzone = GetSubZoneText(),
    locale = GetLocale(),
    clientVersion = version,
    clientBuild = build,
    interface = interface,
    addonVersion = ns.VERSION,
  }
end
