local addonName, ns = ...

ns.VERSION = "0.1.0"
-- Bump when the shape of CrowleyDB.scans changes; the server keys its parser off this.
ns.SCAN_FORMAT = 1
ns.MAX_STORED_SCANS = 6

local defaults = {
  -- Manual overrides for the house a scan is attributed to. nil = auto-detect.
  settings = {},
  scans = {},
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
  for _, id in ipairs(CROWLEY_DATA.ackedScans) do acked[id] = true end

  local remaining = {}
  local dropped = 0
  for id, scan in pairs(db.scans) do
    if acked[id] then
      dropped = dropped + 1
    else
      remaining[#remaining + 1] = scan
    end
  end

  table.sort(remaining, function(a, b) return a.finishedAt > b.finishedAt end)
  db.scans = {}
  for i = 1, math.min(#remaining, ns.MAX_STORED_SCANS) do
    db.scans[remaining[i].id] = remaining[i]
  end

  if #remaining > ns.MAX_STORED_SCANS then
    ns.Print(("dropped %d un-uploaded scan(s) over the %d scan limit; is the companion running?")
      :format(#remaining - ns.MAX_STORED_SCANS, ns.MAX_STORED_SCANS))
  end
  if dropped > 0 then
    ns.Print(("cleared %d uploaded scan(s)"):format(dropped))
  end
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
  pruneScans(ns.db)
end)

ns.On("AUCTION_HOUSE_SHOW", function()
  local house = ns.Context.House()
  ns.Print(("AH open - scans will be saved to |cffffd200%s|r (%s). /crowley scan to start.")
    :format(house.key, house.source))
end)
