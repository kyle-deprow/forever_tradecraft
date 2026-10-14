local _, ns = ...

local Scanner = {}
ns.Scanner = Scanner

local BATCH_SIZE = 500
local SCAN_COOLDOWN = 15 * 60 -- the client allows one full scan per 15 minutes

local state -- nil when idle

ns.ahOpen = false
ns.On("AUCTION_HOUSE_SHOW", function() ns.ahOpen = true end)
ns.On("AUCTION_HOUSE_CLOSED", function()
  ns.ahOpen = false
  if state then Scanner.Abort("auction house closed") end
end)

-- Identity of what is being sold: item ID, plus random suffix and bonus IDs, which make
-- otherwise identical items differ in value. Field positions follow the itemString layout:
-- itemID:enchant:gem1:gem2:gem3:gem4:suffixID:uniqueID:linkLevel:specID:modifiersMask:
-- context:numBonusIDs:bonusID...
function Scanner.ItemKey(link)
  local parts = {}
  for field in (link:match("item:([%-%d:]+)") .. ":"):gmatch("([^:]*):") do
    parts[#parts + 1] = field
  end
  local key = parts[1]
  local suffix = tonumber(parts[7])
  if suffix and suffix ~= 0 then key = key .. ":s" .. suffix end
  local numBonus = tonumber(parts[13]) or 0
  if numBonus > 0 then
    local bonuses = {}
    for i = 14, 13 + numBonus do bonuses[#bonuses + 1] = tonumber(parts[i]) end
    table.sort(bonuses)
    key = key .. ":b" .. table.concat(bonuses, ".")
  end
  return key
end

function Scanner.InProgress() return state ~= nil end

function Scanner.CooldownRemaining()
  if not ns.db.lastScanAt then return 0 end
  return math.max(0, SCAN_COOLDOWN - (time() - ns.db.lastScanAt))
end

function Scanner.Start(force)
  if state then return ns.Print("a scan is already running") end
  if not ns.ahOpen then return ns.Print("open the auction house first") end

  local wait = Scanner.CooldownRemaining()
  if wait > 0 and not force then
    return ns.Print(("full scan is on cooldown for %dm%02ds (/crowley scan force to try anyway)")
      :format(math.floor(wait / 60), wait % 60))
  end

  local house = ns.Context.House()
  state = {
    house = house,
    context = ns.Context.Snapshot(),
    startedAt = time(),
    rows = {},
    items = {},
    pending = {},
    skipped = 0,
  }
  state.onData = function()
    ns.Off("REPLICATE_ITEM_LIST_UPDATE", state.onData)
    Scanner.Collect()
  end
  ns.On("REPLICATE_ITEM_LIST_UPDATE", state.onData)

  ns.Print(("scanning %s..."):format(house.key))
  C_AuctionHouse.ReplicateItems()
end

function Scanner.Abort(reason)
  if not state.collecting then ns.Off("REPLICATE_ITEM_LIST_UPDATE", state.onData) end
  state = nil
  ns.Print("scan aborted: " .. reason)
end

-- GetReplicateItemInfo returns: name, texture, count, quality, usable, level, levelType,
-- minBid, minIncrement, buyout, bidAmount, highBidder, bidderFullName, owner,
-- ownerFullName, saleStatus, itemID, hasAllInfo. Buyout is for the whole auction.
local function recordRow(s, i, info)
  local key = Scanner.ItemKey(C_AuctionHouse.GetReplicateItemLink(i))
  s.rows[#s.rows + 1] = table.concat({
    info[17],
    key,
    info[3],
    info[10],
    info[8],
    info[11],
    -- Enum.AuctionHouseTimeLeftBand is 0-3; stored as 1 (short) .. 4 (very long).
    C_AuctionHouse.GetReplicateItemTimeLeft(i) + 1,
    info[14] or "", -- nil when the seller is hidden
  }, ",")
  s.items[key] = s.items[key] or { n = info[1], q = info[4], l = info[6] }
end

function Scanner.Collect()
  local s = state
  s.collecting = true
  local last = C_AuctionHouse.GetNumReplicateItems() - 1
  ns.Print(("received %d auctions, processing..."):format(last + 1))

  local function batch(from)
    if state ~= s then return end
    for i = from, math.min(from + BATCH_SIZE - 1, last) do
      local info = { C_AuctionHouse.GetReplicateItemInfo(i) }
      if not C_Item.DoesItemExistByID(info[17]) then
        -- The server occasionally returns auctions for items that don't exist.
        s.skipped = s.skipped + 1
      elseif info[18] then
        recordRow(s, i, info)
      else
        s.pending[#s.pending + 1] = i
        C_Item.RequestLoadItemDataByID(info[17])
      end
    end
    if from + BATCH_SIZE <= last then
      C_Timer.After(0, function() batch(from + BATCH_SIZE) end)
    else
      Scanner.ResolvePending()
    end
  end
  batch(0)
end

-- Items the client hasn't cached arrive asynchronously; re-check them until all are loaded.
function Scanner.ResolvePending()
  local s = state
  if #s.pending == 0 then return Scanner.Finish() end
  C_Timer.After(1, function()
    if state ~= s then return end
    local stillPending = {}
    for _, i in ipairs(s.pending) do
      local info = { C_AuctionHouse.GetReplicateItemInfo(i) }
      if info[18] then
        recordRow(s, i, info)
      else
        stillPending[#stillPending + 1] = i
      end
    end
    s.pending = stillPending
    Scanner.ResolvePending()
  end)
end

function Scanner.Finish()
  local s = state
  state = nil

  local finishedAt = time()
  local id = ("%s-%d-%s-%04d"):format(s.house.key, finishedAt, s.context.character, math.random(0, 9999))
  local compressed = C_EncodingUtil.CompressString(table.concat(s.rows, "\n"), Enum.CompressionMethod.Deflate)

  ns.db.scans[id] = {
    id = id,
    format = ns.SCAN_FORMAT,
    house = s.house,
    context = s.context,
    startedAt = s.startedAt,
    finishedAt = finishedAt,
    numRows = #s.rows,
    skipped = s.skipped,
    -- Raw deflate, base64; rows are "itemId,itemKey,quantity,buyout,minBid,bid,timeLeft,owner".
    rows = C_EncodingUtil.EncodeBase64(compressed),
    items = s.items,
  }
  ns.db.lastScanAt = finishedAt

  local count = 0
  for _ in pairs(ns.db.scans) do count = count + 1 end
  ns.Print(("scan saved: %d auctions for %s (%d skipped). %d scan(s) waiting - /reload to upload.")
    :format(#s.rows, s.house.key, s.skipped, count))
end
