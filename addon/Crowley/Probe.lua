local _, ns = ...

-- Records the client's AH and encoding API surface so the assumptions the scanner makes
-- about the Forever client can be checked from SavedVariables.
local NAMESPACES = {
  "C_AuctionHouse",
  "C_EncodingUtil",
  "C_GameRules",
  "C_Item",
  "C_RealmInfo",
}

local MOTION_APIS = {
  "UnitPosition",
  "GetPlayerFacing",
  "GetUnitSpeed",
  "UnitAffectingCombat",
  "UnitIsDeadOrGhost",
  "GetBindingKey",
}

local MOTION_BINDINGS = {
  "MOVEFORWARD",
  "MOVEBACKWARD",
  "STRAFELEFT",
  "STRAFERIGHT",
  "TURNLEFT",
}

local function functionNames(t)
  local keys = {}
  for k, v in pairs(t) do
    if type(v) == "function" then keys[#keys + 1] = k end
  end
  table.sort(keys)
  return keys
end

function ns.Probe()
  local realmName = GetRealmName()
  local region = GetCurrentRegion()
  local regionName = GetCurrentRegionName()
  local snapshotOK, contextOrError = pcall(ns.Context.Snapshot)
  local _, build, _, interface = GetBuildInfo()
  local result = {
    at = time(),
    context = snapshotOK and contextOrError or false,
    -- These are raw native values. Keep them separate from Context.Snapshot(),
    -- whose shape is part of the strict scan envelope.
    region = region,
    regionName = regionName,
    realmName = realmName,
    namespaces = {},
    -- Presence is diagnostic only.  The Agent samples and validates the
    -- actual native values; Probe must not invent values or alter the scan
    -- Context.Snapshot envelope.
    motion = { apiPresence = {}, bindingActions = {} },
  }
  if not snapshotOK then result.contextError = tostring(contextOrError) end

  -- House detection is diagnostic here: an unrecognized client value must not
  -- prevent the raw client facts and API surface from being saved.
  local houseOK, houseOrError = pcall(ns.Context.House)
  if houseOK then
    result.house = houseOrError
  else
    result.house = false
    result.attributionError = tostring(houseOrError)
  end

  for _, name in ipairs(NAMESPACES) do
    result.namespaces[name] = _G[name] and functionNames(_G[name]) or false
  end
  for _, name in ipairs(MOTION_APIS) do
    result.motion.apiPresence[name] = type(_G[name]) == "function"
  end
  for _, action in ipairs(MOTION_BINDINGS) do
    result.motion.bindingActions[#result.motion.bindingActions + 1] = action
  end
  ns.db.probe = result
  local houseText = result.house and result.house.key or ("attribution error: " .. (result.attributionError or "unknown"))
  local messageInterface = result.context and result.context.interface or interface
  local messageBuild = result.context and result.context.clientBuild or build
  ns.Print(("probe: interface %d build %s, house %s - /reload so the companion uploads it")
    :format(messageInterface, messageBuild, houseText))
end
