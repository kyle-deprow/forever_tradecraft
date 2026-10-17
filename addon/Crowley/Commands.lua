local _, ns = ...

local HELP = {
  "/crowley scan [force] - targeted watchlist sweep into the current house",
  "/crowley status - current house, next sweep, stored sweeps, data age",
  "/crowley set <region|ruleset|faction> <value|auto> - override house detection",
  "/crowley lists - push Crowley shopping lists into Auctionator",
  "/crowley probe - record which AH APIs this client has",
}
-- Reserved for the local repeating-session controller.  It is intentionally
-- absent from help and accepts no arguments; the controller must prove this
-- exact preparation command before issuing the normal /logout.
local SESSION_FENCE = "session"

local function status()
  local house = ns.Context.House()
  ns.Print(("house: |cffffd200%s|r (%s)"):format(house.key, house.source))

  local stored = 0
  for _ in pairs(ns.db.scans) do stored = stored + 1 end
  local wait = ns.Scanner.CooldownRemaining()
  local plan = CROWLEY_DATA.scanPlan
  local planText = plan and plan.planHash and plan.planHash:sub(1, 12) or "none"
  ns.Print(("stored sweeps: %d, next sweep: %s%s, plan: %s, cursor: %s, last: %d/%d attempted, %d failed"):format(stored,
    wait > 0 and ("%dm%02ds"):format(math.floor(wait / 60), wait % 60) or "ready",
    ns.Scanner.InProgress() and " (scan running)" or "", planText, ns.db.cursorItemID or "start",
    ns.db.lastSweepAttempted or 0, ns.db.lastSweepPlanned or 0, ns.db.lastSweepFailures or ns.db.failureCount or 0))
  if ns.db.storageBlocked then ns.Print("storage blocked: upload acknowledged sweeps, then /reload again to resume") end
  ns.Print("sweeps upload from SavedVariables on /reload; loaded acknowledgements resume collection after a second /reload")

  if ns.Agent and ns.Scanner.Status then
    local agent = ns.Scanner.Status()
    ns.Print(("agent: %s, ordinal %d/%d, pending %d, loaded acks %d"):format(
      agent.phase, agent.ordinal or 0, agent.planned or 0, #(agent.pending or {}), #(agent.loaded or {})))
  end

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
  local setting
  if value == "auto" then
    setting = nil
  elseif valid[value] then
    setting = value
  else
    local options = {}
    for k in pairs(valid) do options[#options + 1] = k end
    table.sort(options)
    return ns.Print(("%s must be one of: %s, auto"):format(field, table.concat(options, ", ")))
  end
  if ns.Scanner.InProgress() then ns.Scanner.Abort("house_changed") end
  ns.db.settings[field] = setting
  ns.Print(("house is now |cffffd200%s|r"):format(ns.Context.House().key))
end

SLASH_CROWLEY1 = "/crowley"
SlashCmdList.CROWLEY = function(msg)
  local args = {}
  for word in (msg or ""):gmatch("%S+") do args[#args + 1] = word end
  local cmd = (args[1] or ""):lower()

  if cmd == "scan" then
    ns.Scanner.Start(args[2] == "force")
  elseif cmd == SESSION_FENCE and args[2] == "fence" and not args[3] then
    local armed, reason = ns.Scanner.PreLogoutFence()
    if armed then
      ns.Print("session fence armed: automatic starts revoked")
    else
      ns.Print("session fence refused: " .. tostring(reason))
    end
  elseif cmd == "agent" and not args[3] and ns.Agent then
    local ok, reason
    if args[2] == "hold" then
      ok, reason = ns.Agent.Hold()
    elseif args[2] == "measure" then
      ok, reason = ns.Agent.Measure()
    elseif args[2] == "resume" then
      ok, reason = ns.Agent.Resume()
    end
    if ok then
      ns.Print("agent " .. args[2] .. " accepted")
    elseif reason then
      ns.Print("agent " .. tostring(args[2]) .. " refused: " .. tostring(reason))
    else
      for _, line in ipairs(HELP) do ns.Print(line) end
    end
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
