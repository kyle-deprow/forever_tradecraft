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
