local _, ns = ...

-- Records the client's AH and encoding API surface so the assumptions the scanner makes
-- about the Forever client can be checked from SavedVariables.
local NAMESPACES = { "C_AuctionHouse", "C_EncodingUtil", "C_Item" }

local function functionNames(t)
  local keys = {}
  for k, v in pairs(t) do
    if type(v) == "function" then keys[#keys + 1] = k end
  end
  table.sort(keys)
  return keys
end

function ns.Probe()
  local result = {
    at = time(),
    context = ns.Context.Snapshot(),
    house = ns.Context.House(),
    namespaces = {},
  }
  for _, name in ipairs(NAMESPACES) do
    result.namespaces[name] = _G[name] and functionNames(_G[name]) or false
  end
  ns.db.probe = result
  ns.Print(("probe: interface %d build %s, house %s - /reload so the companion uploads it")
    :format(result.context.interface, result.context.clientBuild, result.house.key))
end
