local _, ns = ...

local HELP = {
  "/crowley scan [force] - full AH scan into the current house",
  "/crowley status - current house, cooldown, stored scans, data age",
  "/crowley set <region|ruleset|faction> <value|auto> - override house detection",
  "/crowley lists - push Crowley shopping lists into Auctionator",
  "/crowley probe - record which AH APIs this client has",
}

local function status()
  local house = ns.Context.House()
  ns.Print(("house: |cffffd200%s|r (%s)"):format(house.key, house.source))

  local stored = 0
  for _ in pairs(ns.db.scans) do stored = stored + 1 end
  local wait = ns.Scanner.CooldownRemaining()
  ns.Print(("stored scans: %d, scan cooldown: %s%s"):format(stored,
    wait > 0 and ("%dm%02ds"):format(math.floor(wait / 60), wait % 60) or "ready",
    ns.Scanner.InProgress() and " (scan running)" or ""))

  if CROWLEY_DATA.generatedAt > 0 then
    ns.Print(("strategy data: %d min old"):format(math.floor((time() - CROWLEY_DATA.generatedAt) / 60)))
  else
    ns.Print("strategy data: none yet (start the companion, then /reload)")
  end
end

local function set(field, value)
  local valid = field and ns.Context.VALID[field]
  if not valid then
    return ns.Print("usage: /crowley set <region|ruleset|faction> <value|auto>")
  end
  value = value and value:lower() or ""
  if value == "auto" then
    ns.db.settings[field] = nil
  elseif valid[value] then
    ns.db.settings[field] = value
  else
    local options = {}
    for k in pairs(valid) do options[#options + 1] = k end
    table.sort(options)
    return ns.Print(("%s must be one of: %s, auto"):format(field, table.concat(options, ", ")))
  end
  ns.Print(("house is now |cffffd200%s|r"):format(ns.Context.House().key))
end

SLASH_CROWLEY1 = "/crowley"
SlashCmdList.CROWLEY = function(msg)
  local args = {}
  for word in (msg or ""):gmatch("%S+") do args[#args + 1] = word end
  local cmd = (args[1] or ""):lower()

  if cmd == "scan" then
    ns.Scanner.Start(args[2] == "force")
  elseif cmd == "status" then
    status()
  elseif cmd == "set" then
    set(args[2] and args[2]:lower(), args[3])
  elseif cmd == "lists" then
    local houseKey = ns.Context.House().key
    ns.Print(("synced %d shopping list(s) to Auctionator for %s")
      :format(ns.Bridge.SyncShoppingLists(houseKey), houseKey))
  elseif cmd == "probe" then
    ns.Probe()
  else
    for _, line in ipairs(HELP) do ns.Print(line) end
  end
end
