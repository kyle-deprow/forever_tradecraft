local _, ns = ...

-- Targeted retail-style queries only.  The scanner deliberately uses the documented
-- AuctionHouse ItemKey/result structures and never falls back to the old replication API.
local Scanner = {}
ns.Scanner = Scanner

local CADENCE = 900
local ITEM_TIMEOUT = 30
local OWNED_TIMEOUT = 30
local SWEEP_TIMEOUT = 600
local MAX_PAGES = 10
local MAX_SAFE = 9007199254740991
local state
local generation = 0
local scheduleToken = 0
local internalSendDepth = 0

local function markForeignSearch()
  if internalSendDepth > 0 or not state then return end
  if state.item then state.item.reasonCode = "identity_mismatch" end
end

local function markForeignOwned()
  if internalSendDepth > 0 or not state or not state.ownedHandler then return end
  state.ownedExternal = true
end

if not hooksecurefunc then error("Crowley requires hooksecurefunc for Auction House query attribution") end
hooksecurefunc(C_AuctionHouse, "SendSellSearchQuery", markForeignSearch)
hooksecurefunc(C_AuctionHouse, "SendSearchQuery", markForeignSearch)
hooksecurefunc(C_AuctionHouse, "RequestMoreCommoditySearchResults", markForeignSearch)
hooksecurefunc(C_AuctionHouse, "RequestMoreItemSearchResults", markForeignSearch)
hooksecurefunc(C_AuctionHouse, "QueryOwnedAuctions", markForeignOwned)

ns.ahOpen = false
ns.On("AUCTION_HOUSE_SHOW", function() ns.ahOpen = true Scanner.Schedule() end)
ns.On("AUCTION_HOUSE_CLOSED", function()
  ns.ahOpen = false
  scheduleToken = scheduleToken + 1
  if state then Scanner.Abort("ah_closed") end
end)
ns.On("PLAYER_LOGOUT", function() if state then Scanner.Abort("logout") end end)

local function safeProduct(a, b)
  if type(a) ~= "number" or type(b) ~= "number" or a < 0 or b < 0 or a > MAX_SAFE or b > MAX_SAFE then return nil end
  if a ~= 0 and b > math.floor(MAX_SAFE / a) then return nil end
  return a * b
end

local function compare(a, b)
  local left = safeProduct(a.numerator, b.denominator)
  local right = safeProduct(b.numerator, a.denominator)
  if not left or not right then return nil end
  if left < right then return -1 elseif left > right then return 1 end
  return 0
end

local function gcd(a, b)
  while b ~= 0 do a, b = b, a % b end
  return a
end

local function rational(numerator, denominator)
  if type(numerator) ~= "number" or type(denominator) ~= "number" or numerator < 0 or denominator <= 0 or
      numerator > MAX_SAFE or denominator > MAX_SAFE or numerator ~= math.floor(numerator) or denominator ~= math.floor(denominator) then return nil end
  local divisor = gcd(numerator, denominator)
  return { numerator = numerator / divisor, denominator = denominator / divisor }
end

local function keyFields(key)
  if type(key) ~= "table" then return nil end
  local itemID, itemLevel, itemSuffix, pet = key.itemID, key.itemLevel, key.itemSuffix, key.battlePetSpeciesID
  if type(itemID) ~= "number" or type(itemLevel) ~= "number" or type(itemSuffix) ~= "number" or type(pet) ~= "number" then return nil end
  if itemID <= 0 or itemID > MAX_SAFE or itemLevel < 0 or itemLevel > MAX_SAFE or itemSuffix < 0 or itemSuffix > MAX_SAFE or pet < 0 or pet > MAX_SAFE or
      itemID ~= math.floor(itemID) or itemLevel ~= math.floor(itemLevel) or itemSuffix ~= math.floor(itemSuffix) or pet ~= math.floor(pet) then return nil end
  return itemID, itemLevel, itemSuffix, pet
end

local function keysEqual(left, right)
  local li, ll, ls, lp = keyFields(left)
  local ri, rl, rs, rp = keyFields(right)
  return li and ri and li == ri and ll == rl and ls == rs and lp == rp
end

local function ownerObject(info, commodity)
  local names = {}
  local listed = info.owners
  if type(listed) ~= "table" then return nil end
  for _, owner in ipairs(listed) do
    if type(owner) ~= "string" or owner == "" then return nil end
    names[owner] = true
  end
  local count = info.totalNumberOfOwners
  if type(count) ~= "number" or count < 0 or count > MAX_SAFE or count ~= math.floor(count) or count < #listed then return nil end
  local containsOwner = info.containsOwnerItem
  local containsAccount = info.containsAccountItem
  if type(containsOwner) ~= "boolean" or type(containsAccount) ~= "boolean" then return nil end
  local grouped = commodity or count > 1 or #listed > 1 or containsOwner or containsAccount
  local identity = grouped and "grouped" or (#listed == 1 and count == 1 and "individual" or "unknown")
  return { names = names, totalNumberOfOwners = count, containsOwnerItem = containsOwner,
    containsAccountItem = containsAccount, identityKind = identity }
end

local function timeLeft(info)
  if type(info.timeLeftSeconds) == "number" then
    if info.timeLeftSeconds < 0 or info.timeLeftSeconds > MAX_SAFE or info.timeLeftSeconds ~= math.floor(info.timeLeftSeconds) then return nil end
    return { kind = "exact", seconds = info.timeLeftSeconds }
  end
  if info.timeLeft ~= nil and C_AuctionHouse.GetTimeLeftBandInfo then
    local minimum, maximum = C_AuctionHouse.GetTimeLeftBandInfo(info.timeLeft)
    if type(info.timeLeft) == "number" and info.timeLeft >= 0 and info.timeLeft <= 3 and minimum and maximum and
        minimum >= 0 and maximum >= minimum and minimum <= MAX_SAFE and maximum <= MAX_SAFE and
        minimum == math.floor(minimum) and maximum == math.floor(maximum) then
      return { kind = "band", band = info.timeLeft, minimumSeconds = minimum, maximumSeconds = maximum }
    end
  end
  return { kind = "unknown" }
end

-- Parse only the identity fields carried in an item link.  Bonus IDs are not exposed by
-- ItemSearchResultInfo; they are therefore taken from the documented link when present.
local function linkIdentity(link)
  if type(link) ~= "string" then return nil end
  local text = link:match("item:([%-%d:]+)")
  if not text then return nil end
  local fields = {}
  for field in (text .. ":"):gmatch("([^:]*):") do fields[#fields + 1] = field end
  local itemID = tonumber(fields[1])
  local suffix = tonumber(fields[7]) or 0
  local number = tonumber(fields[13]) or 0
  if not itemID or not suffix or not number or itemID <= 0 or itemID > MAX_SAFE or suffix < 0 or suffix > MAX_SAFE or number < 0 or number > 100 or
      itemID ~= math.floor(itemID) or suffix ~= math.floor(suffix) or number ~= math.floor(number) then return nil end
  local bonuses = {}
  for i = 14, 13 + number do
    local bonus = tonumber(fields[i])
    if not bonus or bonus <= 0 or bonus > MAX_SAFE or bonus ~= math.floor(bonus) then return nil end
    bonuses[tostring(i - 14)] = bonus
  end
  return itemID, suffix, bonuses
end

local function rawKey(itemKey, itemID, link)
  local keyID, level, suffix, pet = keyFields(itemKey)
  if not keyID or keyID ~= itemID then return nil end
  local linkedID, linkedSuffix, bonuses = linkIdentity(link)
  if linkedID and (linkedID ~= itemID or linkedSuffix ~= suffix) then return nil end
  return { itemID = itemID, itemLevel = level, itemSuffix = suffix, battlePetSpeciesID = pet, bonusIDs = bonuses or {} }
end

function Scanner.ItemKey(link, raw)
  if type(raw) ~= "table" then return nil end
  local itemID, level, suffix, pet = raw.itemID, raw.itemLevel, raw.itemSuffix, raw.battlePetSpeciesID
  if type(itemID) ~= "number" or type(level) ~= "number" or type(suffix) ~= "number" or type(pet) ~= "number" then return nil end
  local linkedID, linkedSuffix, linkedBonuses = linkIdentity(link)
  if not linkedID or linkedID ~= itemID or linkedSuffix ~= suffix then return nil end
  local parts = { tostring(itemID) }
  if suffix ~= 0 then parts[#parts + 1] = "s" .. suffix end
  local bonusValues = {}
  for _, bonus in pairs(raw.bonusIDs or {}) do bonusValues[#bonusValues + 1] = bonus end
  table.sort(bonusValues)
  if #bonusValues > 0 then parts[#parts + 1] = "b" .. table.concat(bonusValues, ".") end
  if level ~= 0 then parts[#parts + 1] = "l" .. level end
  if pet ~= 0 then parts[#parts + 1] = "p" .. pet end
  -- The parser and client use the same canonical form; reject a mismatching link instead
  -- of silently collapsing a variant.  An empty bonus table is valid for ordinary items.
  local linkedValues = {}
  for _, bonus in pairs(linkedBonuses or {}) do linkedValues[#linkedValues + 1] = bonus end
  table.sort(linkedValues)
  if #linkedValues ~= #bonusValues then return nil end
  for i = 1, #linkedValues do if linkedValues[i] ~= bonusValues[i] then return nil end end
  return table.concat(parts, ":")
end

local function rowMap(rows)
  local result = {}
  for i, row in ipairs(rows) do result["row:" .. i] = row end
  return result
end

local function unqueried(itemID, ordinal, reason)
  return { itemID = itemID, ordinal = ordinal, kind = "unknown", query = { kind = "unqueried" },
    coverage = "unqueried", sourceComplete = false, cutoff = { kind = "unknown" },
    higherPriceWitness = { kind = "unknown" }, reasonCode = reason or "not_started", rowCount = 0, rows = {} }
end

local function disconnectQueryEvents(s)
  if not s or not s.handlers then return end
  for event, handler in pairs(s.handlers) do ns.Off(event, handler) end
  s.handlers = {}
end

local function sessionAlive(token, owner)
  if not state or state.generation ~= token then return false end
  if owner == state then return true end
  return state.item == owner
end

local function sendMessage(owner, fn)
  if not C_AuctionHouse.IsThrottledMessageSystemReady then error("Crowley requires IsThrottledMessageSystemReady") end
  ns.db.querySendTimes = ns.db.querySendTimes or {}
  local now = time()
  local kept = {}
  for _, sent in ipairs(ns.db.querySendTimes) do if now - sent < 60 then kept[#kept + 1] = sent end end
  ns.db.querySendTimes = kept
  local token = state and state.generation
  if #kept >= 100 or not C_AuctionHouse.IsThrottledMessageSystemReady() then
    C_Timer.After(1, function() if sessionAlive(token, owner) then sendMessage(owner, fn) end end)
    return false
  end
  ns.db.querySendTimes[#ns.db.querySendTimes + 1] = now
  fn()
  return true
end

local function markTail(reason)
  if not state then return end
  for i = state.nextOrdinal, #state.order do
    local itemID = state.order[i]
    if not state.observations[tostring(itemID)] then state.observations[tostring(itemID)] = unqueried(itemID, i, reason) end
  end
end

local function normalizeRows(s, reason)
  local unsafe = false
  local unexpected = false
  for left = 1, #s.rows do
    for right = left + 1, #s.rows do
      local relation = compare(s.rows[left].unitPrice, s.rows[right].unitPrice)
      if not relation then
        unsafe = true
      elseif s.kind == "commodity" and relation > 0 then
        unexpected = true
      end
    end
  end
  if unsafe then return "numeric_range" end
  if unexpected and not reason then reason = "unexpected_order" end
  table.sort(s.rows, function(a, b)
    local relation = compare(a.unitPrice, b.unitPrice)
    return relation and relation < 0 or false
  end)
  return reason
end

local function failCurrent(reason)
  if not state or not state.item then return end
  local s = state.item
  disconnectQueryEvents(s)
  reason = normalizeRows(s, reason)
  local finished = time()
  state.observations[tostring(s.itemID)] = {
    itemID = s.itemID, ordinal = s.ordinal, kind = s.kind or "unknown",
    query = { kind = "queried", startedAt = s.queryStarted, finishedAt = finished }, coverage = "incomplete",
    sourceComplete = false, cutoff = { kind = "unknown" }, higherPriceWitness = { kind = "unknown" },
    reasonCode = reason, rowCount = #s.rows, rows = rowMap(s.rows),
  }
  state.cursor, state.nextOrdinal, state.item = s.itemID, s.ordinal + 1, nil
  ns.db.failureCount = (ns.db.failureCount or 0) + 1
end

local function sourceComplete(s)
  if s.kind == "commodity" then return C_AuctionHouse.HasFullCommoditySearchResults(s.itemID) == true end
  return C_AuctionHouse.HasFullItemSearchResults(s.itemKey) == true
end

local function finishItem(s)
  if not state or state.item ~= s then return end
  disconnectQueryEvents(s)
  local reason = normalizeRows(s, s.reasonCode)
  local complete = false
  if not reason then complete = sourceComplete(s) end
  local depth = s.planLevels
  local levels, previous, cutoff, witness = 0, nil, nil, nil
  if not reason then
    for _, row in ipairs(s.rows) do
      local marker = row.unitPrice.numerator .. ":" .. row.unitPrice.denominator
      if marker ~= previous then levels, previous = levels + 1, marker end
      if levels == depth and not cutoff then cutoff = row.unitPrice end
      if cutoff and compare(row.unitPrice, cutoff) > 0 then witness = row.unitPrice break end
    end
  end
  local coverage, source = "full", complete
  if reason then coverage, source, cutoff, witness = "incomplete", false, { kind = "unknown" }, { kind = "unknown" }
  elseif cutoff and witness then
    local retained = {}
    for _, row in ipairs(s.rows) do if compare(row.unitPrice, cutoff) <= 0 then retained[#retained + 1] = row end end
    s.rows = retained
    coverage = "bounded"
  elseif not complete then
    -- An incomplete commodity cannot claim full coverage without a proven depth boundary;
    -- item results always wait for HasFullItemSearchResults before reaching this branch.
    coverage, source = "incomplete", false
  end
  if s.kind == "item" and coverage == "bounded" and not complete then coverage, source, cutoff, witness = "incomplete", false, { kind = "unknown" }, { kind = "unknown" } end
  local cutoffWire = cutoff and cutoff.numerator and { kind = "price", numerator = cutoff.numerator, denominator = cutoff.denominator } or
    (coverage == "incomplete" and { kind = "unknown" } or { kind = "unbounded" })
  local witnessWire = witness and witness.numerator and { kind = "known", numerator = witness.numerator, denominator = witness.denominator } or { kind = "unknown" }
  state.observations[tostring(s.itemID)] = {
    itemID = s.itemID, ordinal = s.ordinal, kind = s.kind,
    query = { kind = "queried", startedAt = s.queryStarted, finishedAt = time() }, coverage = coverage,
    sourceComplete = source, cutoff = cutoffWire, higherPriceWitness = witnessWire, reasonCode = reason or "ok",
    rowCount = #s.rows, rows = rowMap(s.rows),
  }
  state.cursor, state.nextOrdinal, state.item = s.itemID, s.ordinal + 1, nil
  Scanner.Next()
end

local function resultInfo(s, index)
  local info
  if s.kind == "commodity" then info = C_AuctionHouse.GetCommoditySearchResultInfo(s.itemID, index)
  else info = C_AuctionHouse.GetItemSearchResultInfo(s.itemKey, index) end
  if not info then return nil, "missing_result" end
  local link = info.itemLink
  local rowItemID, key, raw
  if s.kind == "commodity" then
    rowItemID = info.itemID
    if type(rowItemID) ~= "number" or rowItemID ~= s.itemID then return nil, "identity_mismatch" end
    key = tostring(rowItemID)
    raw = { itemID = rowItemID, itemLevel = 0, itemSuffix = 0, battlePetSpeciesID = 0, bonusIDs = {} }
  else
    local fields = info.itemKey and keyFields(info.itemKey)
    if not fields then return nil, "identity_mismatch" end
    rowItemID = fields
    if rowItemID ~= s.itemID or not info.itemLink then return nil, "missing_item_link" end
    raw = rawKey(info.itemKey, rowItemID, info.itemLink)
    key = raw and Scanner.ItemKey(info.itemLink, raw)
    if not key then return nil, "identity_mismatch" end
  end
  local resultID = info.auctionID
  local quantity = info.quantity
  local copper = s.kind == "commodity" and info.unitPrice or info.buyoutAmount
  if type(resultID) ~= "number" or resultID <= 0 or resultID > MAX_SAFE or resultID ~= math.floor(resultID) or
      type(quantity) ~= "number" or quantity <= 0 or quantity ~= math.floor(quantity) or
      type(copper) ~= "number" or copper <= 0 or copper ~= math.floor(copper) or copper > MAX_SAFE or quantity > MAX_SAFE then
    -- A bid-only item is outside the eligible buyout source and is ignored.  Other
    -- malformed source values are surfaced to the observation as incomplete.
    if s.kind == "item" and (info.buyoutAmount == nil or info.buyoutAmount == 0) then return nil, "eligible_skip" end
    return nil, "numeric_range"
  end
  local unit = s.kind == "commodity" and rational(copper, 1) or rational(copper, quantity)
  if not unit then return nil, "numeric_range" end
  local owners = ownerObject(info, s.kind == "commodity")
  if not owners then return nil, "identity_mismatch" end
  local left = timeLeft(info)
  if not left then return nil, "numeric_range" end
  return {
    resultID = resultID, itemID = rowItemID, itemKey = key, rawItemKey = raw,
    link = s.kind == "commodity" and { kind = "unknown" } or { kind = "known", value = info.itemLink },
    quantity = quantity,
    price = { kind = s.kind == "commodity" and "unit" or "auction", copper = copper }, unitPrice = unit,
    owners = owners, timeLeft = left,
  }
end

local function sameNameMap(left, right)
  left, right = left or {}, right or {}
  for name in pairs(left) do
    if not right[name] then return false end
  end
  for name in pairs(right) do
    if not left[name] then return false end
  end
  return true
end

local function sameOwners(left, right)
  return left.totalNumberOfOwners == right.totalNumberOfOwners and
    left.containsOwnerItem == right.containsOwnerItem and
    left.containsAccountItem == right.containsAccountItem and
    left.identityKind == right.identityKind and sameNameMap(left.names, right.names)
end

local function sameRow(left, right)
  local a, b = left.rawItemKey, right.rawItemKey
  return left.itemKey == right.itemKey and left.quantity == right.quantity and
    left.price.kind == right.price.kind and left.price.copper == right.price.copper and
    left.unitPrice.numerator == right.unitPrice.numerator and left.unitPrice.denominator == right.unitPrice.denominator and
    a.itemID == b.itemID and a.itemLevel == b.itemLevel and a.itemSuffix == b.itemSuffix and
    a.battlePetSpeciesID == b.battlePetSpeciesID and sameOwners(left.owners, right.owners)
end

local function collectResults(s)
  if not state or state.item ~= s or not s.awaiting or not s.sentBarrier or not s.responseBarrier then return end
  s.awaiting, s.sentBarrier, s.responseBarrier, s.sentRequested = false, false, false, false
  if s.reasonCode then return finishItem(s) end
  if ns.Context.House().key ~= state.house.key then return Scanner.Abort("house_changed") end
  local count = s.kind == "commodity" and C_AuctionHouse.GetNumCommoditySearchResults(s.itemID) or C_AuctionHouse.GetNumItemSearchResults(s.itemKey)
  local seenThisCall = {}
  for i = 1, count do
    local row, reason = resultInfo(s, i)
    if row then
      if not s.seen[row.resultID] then s.seen[row.resultID] = row s.rows[#s.rows + 1] = row
      elseif not sameRow(s.seen[row.resultID], row) then s.reasonCode = "identity_mismatch" end
    elseif reason ~= "eligible_skip" then
      s.reasonCode = s.reasonCode or (reason == "missing_result" and "identity_mismatch" or reason)
    end
  end
  if s.reasonCode then return finishItem(s) end
  local full = sourceComplete(s)
  local distinct = {}
  for _, row in ipairs(s.rows) do distinct[row.unitPrice.numerator .. ":" .. row.unitPrice.denominator] = true end
  local levelCount = 0 for _ in pairs(distinct) do levelCount = levelCount + 1 end
  if s.kind == "commodity" and levelCount > s.planLevels then
    local partialReason = normalizeRows(s, nil)
    if partialReason then s.reasonCode = partialReason return finishItem(s) end
    local cutoff, witness, levels, previous
    for _, row in ipairs(s.rows) do
      local marker = row.unitPrice.numerator .. ":" .. row.unitPrice.denominator
      if marker ~= previous then
        levels, previous = (levels or 0) + 1, marker
        if levels == s.planLevels then cutoff = row.unitPrice end
      elseif not levels then
        levels = 1
      end
      if cutoff and compare(row.unitPrice, cutoff) > 0 then witness = row.unitPrice break end
    end
    if cutoff and witness then return finishItem(s) end
  end
  if full then return finishItem(s) end
  if s.pages >= MAX_PAGES then failCurrent("page_limit") return Scanner.Next() end
  s.pages = s.pages + 1
  local sent = sendMessage(s, function()
    if state and state.item == s then
      s.sentRequested, s.awaiting, s.sentBarrier, s.responseBarrier = true, false, false, false
      internalSendDepth = internalSendDepth + 1
      if s.kind == "commodity" then C_AuctionHouse.RequestMoreCommoditySearchResults(s.itemID)
      else C_AuctionHouse.RequestMoreItemSearchResults(s.itemKey) end
      internalSendDepth = internalSendDepth - 1
    end
  end)
end

local function bindSearchEvents(s)
  local function commodityEvent(_, itemID)
    if state and state.item == s and s.kind == "commodity" and type(itemID) == "number" and itemID == s.itemID then collectResults(s) end
  end
  local function itemEvent(_, itemKey)
    if state and state.item == s and s.kind == "item" and keysEqual(itemKey, s.itemKey) then collectResults(s) end
  end
  local sentEvent = function()
    if state and state.item == s and s.sentRequested then s.sentBarrier, s.awaiting = true, true end
  end
  local responseEvent = function()
    if state and state.item == s and s.sentRequested and s.sentBarrier then s.responseBarrier = true end
  end
  s.handlers.AUCTION_HOUSE_THROTTLED_MESSAGE_SENT = sentEvent
  s.handlers.AUCTION_HOUSE_THROTTLED_MESSAGE_RESPONSE_RECEIVED = responseEvent
  s.handlers.COMMODITY_SEARCH_RESULTS_ADDED, s.handlers.COMMODITY_SEARCH_RESULTS_UPDATED = commodityEvent, commodityEvent
  s.handlers.ITEM_SEARCH_RESULTS_ADDED, s.handlers.ITEM_SEARCH_RESULTS_UPDATED = itemEvent, itemEvent
  ns.On("AUCTION_HOUSE_THROTTLED_MESSAGE_SENT", sentEvent)
  ns.On("AUCTION_HOUSE_THROTTLED_MESSAGE_RESPONSE_RECEIVED", responseEvent)
  ns.On("COMMODITY_SEARCH_RESULTS_ADDED", commodityEvent) ns.On("COMMODITY_SEARCH_RESULTS_UPDATED", commodityEvent)
  ns.On("ITEM_SEARCH_RESULTS_ADDED", itemEvent) ns.On("ITEM_SEARCH_RESULTS_UPDATED", itemEvent)
end

local function startSearch(s)
  if not state or state.item ~= s then return end
  local metadata = C_AuctionHouse.GetItemKeyInfo(s.itemKey, false)
  if not metadata then return end
  if type(metadata.isCommodity) ~= "boolean" then return failCurrent("metadata_unavailable") end
  s.kind = metadata.isCommodity and "commodity" or "item"
  local sort = s.kind == "commodity" and Enum.AuctionHouseSortOrder.Price or Enum.AuctionHouseSortOrder.Buyout
  s.sorts = { { sortOrder = sort, reverseSort = false } }
  bindSearchEvents(s)
  local sent = sendMessage(s, function()
    if state and state.item == s then
      s.sentRequested, s.awaiting, s.sentBarrier, s.responseBarrier = true, false, false, false
      internalSendDepth = internalSendDepth + 1
      C_AuctionHouse.SendSellSearchQuery(s.itemKey, s.sorts, false)
      internalSendDepth = internalSendDepth - 1
    end
  end)
end

local function disconnectOwned(sweep)
  if not sweep then return end
  if sweep.ownedHandler then ns.Off("OWNED_AUCTIONS_UPDATED", sweep.ownedHandler) end
  if sweep.ownedSentHandler then ns.Off("AUCTION_HOUSE_THROTTLED_MESSAGE_SENT", sweep.ownedSentHandler) end
  if sweep.ownedResponseHandler then ns.Off("AUCTION_HOUSE_THROTTLED_MESSAGE_RESPONSE_RECEIVED", sweep.ownedResponseHandler) end
end

local function failOwned(sweep, reason)
  if state ~= sweep or sweep.owned then return end
  sweep.ownedAwaiting = false
  disconnectOwned(sweep)
  sweep.owned = {
    status = "incomplete", query = { kind = "queried", startedAt = sweep.ownedStarted, finishedAt = time() },
    reasonCode = reason, rowCount = 0, rows = {},
  }
  Scanner.Finish()
end

local function beginOwned(sweep)
  sweep.ownedStarted = time()
  sweep.ownedAwaiting = false
  sweep.ownedHandler = function()
    if state ~= sweep then return end
    if ns.Context.House().key ~= sweep.house.key then return failOwned(sweep, "house_changed") end
    if not sweep.ownedAwaiting or not sweep.ownedSentBarrier or not sweep.ownedResponseBarrier or sweep.ownedExternal then return end
    if not C_AuctionHouse.HasFullOwnedAuctionResults() then return end
    sweep.ownedAwaiting, sweep.ownedSentBarrier, sweep.ownedResponseBarrier, sweep.ownedSentRequested = false, false, false, false
    local rows, invalid = {}, false
      for i = 1, C_AuctionHouse.GetNumOwnedAuctions() do
        local info = C_AuctionHouse.GetOwnedAuctionInfo(i)
        local itemID, keyFieldsValue = info and info.itemKey and keyFields(info.itemKey)
        if not info or type(info.auctionID) ~= "number" or info.auctionID <= 0 or info.auctionID > MAX_SAFE or info.auctionID ~= math.floor(info.auctionID) or
            not itemID or type(info.quantity) ~= "number" or info.quantity <= 0 or info.quantity > MAX_SAFE or info.quantity ~= math.floor(info.quantity) or
            (info.status ~= Enum.AuctionStatus.Active and info.status ~= Enum.AuctionStatus.Sold) or not info.itemLink then
          invalid = true
        else
          local raw = rawKey(info.itemKey, itemID, info.itemLink)
          local key = raw and Scanner.ItemKey(info.itemLink, raw)
          local buyout = info.buyoutAmount
          if not key or (buyout ~= nil and (type(buyout) ~= "number" or buyout < 0 or buyout ~= math.floor(buyout) or buyout > MAX_SAFE)) then invalid = true
          else rows[#rows + 1] = { auctionID = info.auctionID, itemID = itemID, itemKey = key, rawItemKey = raw,
            itemLink = info.itemLink, quantity = info.quantity,
            buyout = buyout and buyout > 0 and { kind = "known", copper = buyout } or { kind = "unknown" },
            status = info.status == Enum.AuctionStatus.Sold and "sold" or "active" }
          end
        end
      end
      sweep.owned = { status = invalid and "incomplete" or "full", query = { kind = "queried", startedAt = sweep.ownedStarted, finishedAt = time() },
        reasonCode = invalid and "query_timeout" or "ok", rowCount = #rows, rows = (function() local out = {} for _, row in ipairs(rows) do out[tostring(row.auctionID)] = row end return out end)() }
      disconnectOwned(sweep)
      Scanner.Finish()
  end
  sweep.ownedSentHandler = function()
    if state == sweep and sweep.ownedSentRequested then sweep.ownedSentBarrier, sweep.ownedAwaiting = true, true end
  end
  sweep.ownedResponseHandler = function()
    if state == sweep and sweep.ownedSentRequested and sweep.ownedSentBarrier then sweep.ownedResponseBarrier = true end
  end
  ns.On("AUCTION_HOUSE_THROTTLED_MESSAGE_SENT", sweep.ownedSentHandler)
  ns.On("AUCTION_HOUSE_THROTTLED_MESSAGE_RESPONSE_RECEIVED", sweep.ownedResponseHandler)
  ns.On("OWNED_AUCTIONS_UPDATED", sweep.ownedHandler)
  sweep.ownedTimer = C_Timer.After(OWNED_TIMEOUT, function()
    if state == sweep and not sweep.owned then
      failOwned(sweep, "query_timeout")
    end
  end)
  local sent = sendMessage(sweep, function()
    if state == sweep then
      sweep.ownedSentRequested, sweep.ownedAwaiting, sweep.ownedSentBarrier, sweep.ownedResponseBarrier = true, false, false, false
      internalSendDepth = internalSendDepth + 1
      sweep.ownedSorts = { { sortOrder = Enum.AuctionHouseSortOrder.Buyout, reverseSort = false } }
      C_AuctionHouse.QueryOwnedAuctions(sweep.ownedSorts)
      internalSendDepth = internalSendDepth - 1
    end
  end)
end

local function beginItem(itemID, ordinal)
  local itemKey = C_AuctionHouse.MakeItemKey(itemID, 0, 0, 0)
  local s = { itemID = itemID, ordinal = ordinal, itemKey = itemKey, rows = {}, seen = {}, pages = 1,
    handlers = {}, queryStarted = time(), planLevels = state.plan.initialPriceLevels }
  state.item, state.cursor = s, itemID
  local metadata = C_AuctionHouse.GetItemKeyInfo(itemKey, false)
  if not metadata then
    s.metadataWaiting = true
    s.handlers.ITEM_KEY_ITEM_INFO_RECEIVED = function(_, readyID)
      if state and state.item == s and readyID == itemID then s.metadataWaiting = false startSearch(s) end
    end
    ns.On("ITEM_KEY_ITEM_INFO_RECEIVED", s.handlers.ITEM_KEY_ITEM_INFO_RECEIVED)
    C_Item.RequestLoadItemDataByID(itemID)
  else startSearch(s) end
  s.timer = C_Timer.After(ITEM_TIMEOUT, function()
    if state and state.item == s then failCurrent(s.metadataWaiting and "metadata_unavailable" or "query_timeout") Scanner.Next() end
  end)
end

function Scanner.Next()
  if not state then return end
  if ns.Context.House().key ~= state.house.key then
    if state.item then failCurrent("house_changed") end
    markTail("house_changed") return Scanner.Finish()
  end
  if time() - state.startedAt >= SWEEP_TIMEOUT then
    if state.item then failCurrent("sweep_timeout") end
    if state.ownedHandler then
      disconnectOwned(state)
      state.owned = { status = "incomplete", query = { kind = "queried", startedAt = state.ownedStarted or time(), finishedAt = time() }, reasonCode = "sweep_timeout", rowCount = 0, rows = {} }
    end
    markTail("sweep_timeout") return Scanner.Finish()
  end
  if state.nextOrdinal > #state.order then
    if state.owned then return Scanner.Finish() end
    return beginOwned(state)
  end
  beginItem(state.order[state.nextOrdinal], state.nextOrdinal)
end

function Scanner.InProgress() return state ~= nil end
function Scanner.CooldownRemaining() if not ns.db.lastSweepStart then return 0 end return math.max(0, CADENCE - (time() - ns.db.lastSweepStart)) end
function Scanner.Due() return Scanner.CooldownRemaining() == 0 end
function Scanner.Schedule()
  if not ns.ahOpen or state or ns.db.storageBlocked then return end
  scheduleToken = scheduleToken + 1
  local token = scheduleToken
  C_Timer.After(Scanner.CooldownRemaining(), function() if token == scheduleToken and ns.ahOpen then Scanner.Start(false) end end)
end

function Scanner.Start(force)
  if state then return ns.Print("a sweep is already running") end
  if not ns.ahOpen then return ns.Print("open the auction house first") end
  if ns.PruneStorage then ns.PruneStorage() end
  local plan, errorText = (function()
    if not CROWLEY_DATA.scanPlan or not CROWLEY_DATA.scanPlan.planJSON then return nil, "no scan plan loaded" end
    if not C_EncodingUtil or not C_EncodingUtil.DeserializeJSON then return nil, "required encoding API unavailable" end
    local loaded = C_EncodingUtil.DeserializeJSON(CROWLEY_DATA.scanPlan.planJSON)
    if not loaded or loaded.schemaVersion ~= 2 or loaded.cadenceSeconds ~= CADENCE or
        type(loaded.initialPriceLevels) ~= "number" or loaded.initialPriceLevels < 1 or loaded.initialPriceLevels ~= math.floor(loaded.initialPriceLevels) or
        type(loaded.itemIDs) ~= "table" or #loaded.itemIDs == 0 then return nil, "invalid scan plan" end
    local previous = 0
    for index, itemID in ipairs(loaded.itemIDs) do
      if type(itemID) ~= "number" or itemID < 1 or itemID ~= math.floor(itemID) or itemID <= previous then return nil, "invalid scan plan" end
      previous = itemID
    end
    return loaded
  end)()
  if not plan then return ns.Print("scan refused: " .. errorText) end
  if ns.db.storageBlocked then return ns.Print("scan paused: storage blocked until acknowledgements are loaded") end
  if not force and not Scanner.Due() then return ns.Print(("scan due in %ds"):format(Scanner.CooldownRemaining())) end
  local cursor = ns.db.cursorItemID
  local found = false for _, itemID in ipairs(plan.itemIDs) do if itemID == cursor then found = true break end end
  if ns.db.cursorPlanHash and ns.db.cursorPlanHash ~= CROWLEY_DATA.scanPlan.planHash then
    if not found then ns.Print("scan plan changed; cursor reset to first item") cursor = nil else ns.Print("scan plan changed; continuing after cursor") end
  elseif cursor and not found then ns.Print("scan cursor no longer exists; reset to first item") cursor = nil end
  scheduleToken = scheduleToken + 1
  generation = generation + 1
  local sweepGeneration = generation
  local sweepPlanHash = CROWLEY_DATA.scanPlan.planHash
  local sweepPlanJSON = CROWLEY_DATA.scanPlan.planJSON
  state = { generation = sweepGeneration, plan = plan, planHash = sweepPlanHash, planJSON = sweepPlanJSON, order = (function()
    local ids, start = {}, 1
    for i, itemID in ipairs(plan.itemIDs) do ids[i] = itemID if itemID == cursor then start = i + 1 end end
    if start > #ids then start = 1 end
    local ordered = {} for n = 0, #ids - 1 do ordered[#ordered + 1] = ids[((start + n - 1) % #ids) + 1] end return ordered
  end)(), nextOrdinal = 1, observations = {}, startedAt = time(), house = ns.Context.House(), context = ns.Context.Snapshot() }
  ns.db.lastSweepStart = state.startedAt
  ns.Print(("sweep started for %s (%d planned items)"):format(state.house.key, #state.order))
  local sweep = state
  C_Timer.After(SWEEP_TIMEOUT, function()
    if state == sweep and state.generation == sweepGeneration then
      if state.item then failCurrent("sweep_timeout") end
      if state.ownedHandler then
        disconnectOwned(state)
        if not state.owned then state.owned = { status = "incomplete", query = { kind = "queried", startedAt = state.ownedStarted or time(), finishedAt = time() }, reasonCode = "sweep_timeout", rowCount = 0, rows = {} } end
      end
      markTail("sweep_timeout") Scanner.Finish()
    end
  end)
  Scanner.Next()
end

function Scanner.Abort(reason)
  if not state then return end
  if state.item then failCurrent(reason) end
  if state.ownedHandler then
    disconnectOwned(state)
    state.owned = { status = "incomplete", query = { kind = "queried", startedAt = state.ownedStarted or time(), finishedAt = time() }, reasonCode = reason, rowCount = 0, rows = {} }
  end
  markTail(reason)
  Scanner.Finish()
end

function Scanner.Finish()
  if not state then return end
  local s = state state = nil
  local owned = s.owned or { status = "unqueried", query = { kind = "unqueried" }, reasonCode = "not_started", rowCount = 0, rows = {} }
  local payload = { planHash = s.planHash, planJSON = s.planJSON, observations = s.observations, owned = owned }
  local compressed = C_EncodingUtil.CompressString(C_EncodingUtil.SerializeJSON(payload), Enum.CompressionMethod.Deflate)
  local id = ("%s-%d-%s-%04d"):format(s.house.key, s.startedAt, s.context.character, math.random(0, 9999))
  ns.db.scans[id] = { id = id, format = 2, house = s.house, context = s.context, startedAt = s.startedAt, finishedAt = time(), numRows = 0,
    numObservations = #s.order, payload = C_EncodingUtil.EncodeBase64(compressed) }
  for _, observation in pairs(s.observations) do ns.db.scans[id].numRows = ns.db.scans[id].numRows + observation.rowCount end
  local stored = 0 for _ in pairs(ns.db.scans) do stored = stored + 1 end
  local attempted, failures = 0, 0
  for _, observation in pairs(s.observations) do
    if observation.query.kind == "queried" then attempted = attempted + 1 end
    if observation.coverage == "incomplete" or observation.coverage == "unqueried" then failures = failures + 1 end
  end
  ns.db.lastSweepPlanned, ns.db.lastSweepAttempted, ns.db.lastSweepFailures = #s.order, attempted, failures
  ns.db.storageBlocked = stored >= ns.MAX_STORED_SCANS
  ns.db.cursorItemID, ns.db.cursorPlanHash = s.cursor, s.planHash
  ns.Print(("sweep saved: %d observations, %d rows for %s - /reload to upload"):format(#s.order, ns.db.scans[id].numRows, s.house.key))
  Scanner.Schedule()
end
