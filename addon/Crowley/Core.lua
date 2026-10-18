local addonName, ns = ...

ns.VERSION = "0.2.0"
-- Bump when the shape of CrowleyDB.scans changes; the server keys its parser off this.
ns.SCAN_FORMAT = 2
ns.MAX_STORED_SCANS = 6

local defaults = {
  -- Manual overrides for the house a scan is attributed to. nil = auto-detect.
  settings = {},
  scans = {}, -- legacy entries are retained only for the flush transition
  sweeps = {},
  cursorItemID = nil,
  cursorPlanHash = nil,
  failureCount = 0,
  lastSweepPlanned = 0,
  lastSweepAttempted = 0,
  lastSweepFailures = 0,
}

-- Native construction is decided once, by Core's first ADDON_LOADED handler.
-- Agent and Scanner consume this immutable per-load decision; malformed
-- SavedVariables are never repaired by a later handler.
local NATIVE_STATES = {
  armed = true, deferred = true, constructing = true, constructed = true,
  failed = true, restore_pending = true,
}

local function copyValue(value)
  if type(value) ~= "table" then return value end
  local result = {}
  for key, child in pairs(value) do result[key] = copyValue(child) end
  return result
end

local function exactKeys(value, allowed)
  if type(value) ~= "table" then return false end
  for key in pairs(value) do if not allowed[key] then return false end end
  for key in pairs(allowed) do if value[key] == nil then return false end end
  return true
end

local function validToken(token, allowRecovery)
  if type(token) ~= "string" or #token < 1 or #token > 64 then return false end
  if token:find("[%c]") then return false end
  if allowRecovery then return token:match("^recovery:[0-9a-f]+$") ~= nil and #token == 33 end
  return token:find("%s") == nil
end

local function validateNativeMarker(marker)
  if type(marker) ~= "table" or not exactKeys(marker, { schema = true, state = true, token = true, attempts = true }) then
    return nil, "malformed"
  end
  if marker.schema ~= 1 or type(marker.attempts) ~= "number" or marker.attempts ~= math.floor(marker.attempts) then
    return nil, "malformed"
  end
  local state = marker.state
  if not NATIVE_STATES[state] then return nil, "malformed" end
  if state == "restore_pending" then
    if marker.attempts ~= 0 or not validToken(marker.token, true) then return nil, "malformed" end
  elseif (state == "armed" or state == "deferred") and marker.attempts ~= 0 then
    return nil, "malformed"
  elseif (state == "constructing" or state == "constructed" or state == "failed") and marker.attempts ~= 1 then
    return nil, "malformed"
  elseif not validToken(marker.token, false) then
    return nil, "malformed"
  end
  return copyValue(marker), nil
end

local function decideNativeConstruction()
  local marker = ns.db.nativeConstruction
  if marker == nil then
    ns.nativeDecision = { kind = "ordinary", state = "ordinary", marker = nil, reason = "" }
    return
  end
  local valid, reason = validateNativeMarker(marker)
  if not valid then
    ns.nativeDecision = { kind = "restore_only", state = "unknown", marker = copyValue(marker), reason = reason }
    return
  end
  -- armed is the only pre-reload spelling. The next load owns the
  -- canonical deferred spelling while retaining the exact boot token.
  if valid.state == "armed" then
    valid.state = "deferred"
    ns.db.nativeConstruction = copyValue(valid)
  end
  ns.nativeDecision = { kind = valid.state, state = valid.state, marker = valid, reason = "" }
end

function ns.NativeDecision()
  return copyValue(ns.nativeDecision or { kind = "unknown", state = "unknown", marker = nil, reason = "not_loaded" })
end

function ns.NativeMarkerValid(marker)
  return validateNativeMarker(marker)
end

function ns.SetNativeMarker(marker)
  local valid, reason = validateNativeMarker(marker)
  if not valid then return false, reason end
  ns.db.nativeConstruction = copyValue(valid)
  return true
end

function ns.Print(...)
  local parts = { ... }
  for i = 1, #parts do parts[i] = tostring(parts[i]) end
  DEFAULT_CHAT_FRAME:AddMessage("|cff4fc3f7Crowley|r: " .. table.concat(parts, " "))
end

-- Scans the companion has confirmed uploading are listed in CROWLEY_DATA.ackedScans;
-- drop them so SavedVariables does not grow without bound.
local function pruneScans(db)
  local acked = {}
  for _, id in ipairs(CROWLEY_DATA.ackedScans or {}) do acked[id] = true end
  for _, id in ipairs(CROWLEY_DATA.ackedSweeps or {}) do acked[id] = true end

  local remaining = {}
  local dropped = 0
  for id, scan in pairs(db.scans or {}) do
    if acked[id] then
      dropped = dropped + 1
    else
      remaining[#remaining + 1] = scan
    end
  end

  table.sort(remaining, function(a, b) return a.finishedAt > b.finishedAt end)
  db.scans = {}
  for i = 1, #remaining do
    db.scans[remaining[i].id] = remaining[i]
  end
  db.storageBlocked = #remaining >= ns.MAX_STORED_SCANS

  if #remaining > ns.MAX_STORED_SCANS then
    ns.Print(("storage blocked: %d unacknowledged legacy scan(s); flush and reload before v2 collection")
      :format(#remaining - ns.MAX_STORED_SCANS))
  end
  if dropped > 0 then
    ns.Print(("cleared %d uploaded scan(s)"):format(dropped))
  end
end

local function pruneSweeps(db)
  local acked = {}
  for _, id in ipairs(CROWLEY_DATA.ackedSweeps or CROWLEY_DATA.ackedScans or {}) do acked[id] = true end
  local remaining = {}
  for id, sweep in pairs(db.sweeps or {}) do
    if not acked[id] then remaining[#remaining + 1] = sweep end
  end
  db.sweeps = {}
  for _, sweep in ipairs(remaining) do db.sweeps[sweep.id] = sweep end
  db.storageBlocked = db.storageBlocked or #remaining >= ns.MAX_STORED_SCANS
  if db.storageBlocked then
    ns.Print(("storage blocked: %d unacknowledged sweep(s); /reload, companion upload, then reload again")
      :format(#remaining))
  end
end

function ns.PruneStorage()
  if not ns.db then return end
  pruneScans(ns.db)
  pruneSweeps(ns.db)
end

ns.frame = CreateFrame("Frame")
ns.handlers = {}

function ns.On(event, fn)
  if not ns.handlers[event] then
    ns.handlers[event] = {}
    ns.frame:RegisterEvent(event)
  end
  table.insert(ns.handlers[event], fn)
end

function ns.Off(event, fn)
  local list = ns.handlers[event]
  for i = #list, 1, -1 do
    if list[i] == fn then table.remove(list, i) end
  end
  if #list == 0 then
    ns.handlers[event] = nil
    ns.frame:UnregisterEvent(event)
  end
end

ns.frame:SetScript("OnEvent", function(_, event, ...)
  -- Copy so handlers can unregister themselves mid-dispatch.
  local snapshot = { unpack(ns.handlers[event]) }
  for _, fn in ipairs(snapshot) do fn(event, ...) end
end)

ns.On("ADDON_LOADED", function(_, name)
  if name ~= addonName then return end
  CrowleyDB = CrowleyDB or {}
  for k, v in pairs(defaults) do
    if CrowleyDB[k] == nil then CrowleyDB[k] = v end
  end
  ns.db = CrowleyDB
  decideNativeConstruction()
  ns.db.cursorItemID = ns.db.cursorItemID
  ns.db.cursorPlanHash = ns.db.cursorPlanHash
  ns.db.failureCount = ns.db.failureCount or 0
  ns.PruneStorage()
  local plan = CROWLEY_DATA.scanPlan
  if plan and plan.planHash then
    ns.Print(("plan loaded: %s (%d item(s))"):format(plan.planHash:sub(1, 12), #(plan.itemIDs or {})))
  else
    ns.Print("plan not loaded; collection is paused until the companion writes Data.lua")
  end
end)

ns.On("AUCTION_HOUSE_SHOW", function()
  local house = ns.Context.House()
  ns.Print(("AH open - scans will be saved to |cffffd200%s|r (%s). /crowley scan to start.")
    :format(house.key, house.source))
end)
