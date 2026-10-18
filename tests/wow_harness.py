"""Runs the real addon Lua under Lua 5.1 (WoW's version) against a fake WoW client API."""

from __future__ import annotations

import base64
import hashlib
import json
import math
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from lupa import lua51
from PIL import Image

from crowley.core.watchlist import load_catalog

ADDONS = Path(__file__).resolve().parents[1] / "addon"
_NEXT_AUCTION_ID = 1
_BYTE_ATLAS_PATH = ADDONS / "Crowley" / "Textures" / "ByteAtlas.tga"
_BYTE_ATLAS: Image.Image | None = None

STUBS = r"""
local harness = ...
_events = {}
_timers = {}
_chat = {}
_now = 1760000000
_profile_ms = 0

function time() return _now end
function GetTime() return _now - 1760000000 end
function GetBuildInfo() return "1.60.1", "70450", "Oct 1 2026", 16001 end
function debugprofilestop() _profile_ms = _profile_ms + 0.01 return _profile_ms end
function collectgarbage(option)
  harness.gcCalls = (harness.gcCalls or 0) + 1
  if option ~= "count" then
    harness.gcMutations = (harness.gcMutations or 0) + 1
    error("harness only exposes the read-only count diagnostic")
  end
  if harness.luaHeapAvailable == false then return nil end
  local values = harness.luaHeapValues
  if values and #values > 0 then
    harness.luaHeapIndex = (harness.luaHeapIndex or 0) + 1
    return values[math.min(harness.luaHeapIndex, #values)]
  end
  return harness.luaHeapValue or 512
end
function UnitName() return "Tester" end
function UnitFactionGroup() return harness.faction end
function GetRealmName() return harness.realm end
function GetZoneText() return harness.zone end
function GetSubZoneText() return harness.subzone end
function GetCurrentRegionName() return harness.regionName end
function GetCurrentRegion() return harness.region end
function GetLocale() return "enUS" end

-- Native movement telemetry APIs.  These return the same value shapes the
-- installed client exposes; Agent.lua is responsible for rejecting absent or
-- malformed values rather than filling in safety defaults.
function UnitPosition(unit)
  if unit ~= "player" then return nil end
  return harness.positionX, harness.positionY, harness.positionZ, harness.positionInstance
end
function GetPlayerFacing() return harness.facing end
function GetUnitSpeed(unit)
  if unit ~= "player" then return nil end
  harness.speedCalls = (harness.speedCalls or 0) + 1
  local tuple = harness.speedTuple
  if tuple then return tuple[1], tuple[2], tuple[3], tuple[4] end
  return harness.speed, harness.speedRun or 0, harness.speedFlight or 0, harness.speedSwim or 0
end
function UnitAffectingCombat(unit)
  if unit ~= "player" then return nil end
  return harness.combat
end
function UnitIsDeadOrGhost(unit)
  if unit ~= "player" then return nil end
  return harness.deadOrGhost
end
function GetBindingKey(action)
  local bindings = harness.bindings
  return bindings and bindings[action]
end

if not harness.ctmMissing then
  C_CVar = {
    GetCVarBool = function(name)
      assert(name == "autointeract", "documented CVar accessor signature")
      harness.ctmCalls = (harness.ctmCalls or 0) + 1
      local mode = harness.ctmMode or "false"
      if mode == "error" then error("CVar accessor error") end
      if mode == "nil" then return nil end
      if mode == "wrong_type" then return "false" end
      return mode == "true"
    end,
  }
end

local function nativePredicate(field, mode, ...)
  harness.groundCalls = harness.groundCalls or {}
  harness.groundArgCounts = harness.groundArgCounts or {}
  harness.groundCalls[field] = (harness.groundCalls[field] or 0) + 1
  harness.groundArgCounts[field] = (harness.groundArgCounts[field] or 0) + select("#", ...)
  mode = mode or "false"
  if mode == "error" then error("native predicate error") end
  if mode == "nil" then return nil end
  if mode == "wrong_type" then return "false" end
  return mode == "true"
end
if not (harness.groundModes and harness.groundModes.flying == "missing") then
  function IsFlying(...) return nativePredicate("flying", harness.groundModes and harness.groundModes.flying, ...) end
end
if not (harness.groundModes and harness.groundModes.falling == "missing") then
  function IsFalling(...) return nativePredicate("falling", harness.groundModes and harness.groundModes.falling, ...) end
end
if not (harness.groundModes and harness.groundModes.swimming == "missing") then
  function IsSwimming(...) return nativePredicate("swimming", harness.groundModes and harness.groundModes.swimming, ...) end
end
if not (harness.groundModes and harness.groundModes.submerged == "missing") then
  function IsSubmerged(...) return nativePredicate("submerged", harness.groundModes and harness.groundModes.submerged, ...) end
end
if not (harness.groundModes and harness.groundModes.mounted == "missing") then
  function IsMounted(...) return nativePredicate("mounted", harness.groundModes and harness.groundModes.mounted, ...) end
end
if not (harness.groundModes and harness.groundModes.taxi == "missing") then
  function UnitOnTaxi(unit, ...)
    assert(unit == "player", "documented UnitOnTaxi signature")
    return nativePredicate("taxi", harness.groundModes and harness.groundModes.taxi, unit, ...)
  end
end

if harness.realmInfo then
  C_RealmInfo = { GetRealmInfo = function() end }
end
if harness.gameRules then
  C_GameRules = {
    GetCurrentGameModeRecordID = function() end,
    GetActiveGameMode = function() end,
    IsHardcoreActive = function() return false end,
    IsStandard = function() return true end,
  }
end

Enum = {
  CompressionMethod = { Deflate = 0 },
  AuctionHouseSortOrder = { Price = 1, Buyout = 2 },
  AuctionStatus = { Active = 0, Sold = 1 },
  ItemClass = { Container = 1, Weapon = 2, Armor = 4, Recipe = 9, Profession = 19, Tradegoods = 7 },
}

DEFAULT_CHAT_FRAME = { AddMessage = function(_, msg) table.insert(_chat, msg) end }
SlashCmdList = {}
UIParent = {
  width = harness.rootWidth or 1365.333374,
  height = harness.rootHeight or 768,
  effectiveScale = harness.rootEffectiveScale or 1,
  name = "UIParent",
}
function UIParent:GetWidth() return self.width end
function UIParent:GetHeight() return self.height end
function UIParent:GetEffectiveScale() return self.effectiveScale end

local chatEdit = harness.chatEdit
function chatEdit:IsShown() return self.shown end
function chatEdit:HasFocus() return self.focused end
function chatEdit:GetText() return self.text end
ChatFrameUtil = { GetActiveWindow = function() return chatEdit.shown and chatEdit or nil end }

function CreateFrame(_, name, parent, template)
  local frame = { events = {}, name = name, parent = parent or UIParent, template = template }
  if name then _G[name] = frame end
  function frame:RegisterEvent(e) self.events[e] = true end
  function frame:UnregisterEvent(e) self.events[e] = nil end
  function frame:SetScript(kind, fn)
    if kind == "OnEvent" then self.onEvent = fn
    elseif kind == "OnUpdate" then self.onUpdate = fn
    elseif kind == "OnClick" then self.onClick = fn
    else self[kind] = fn end
  end
  function frame:SetIgnoreParentScale(value) self.ignoreParentScale = value end
  function frame:GetEffectiveScale()
    if self.ignoreParentScale then return self.scale or 1 end
    local parentScale = self.parent and self.parent:GetEffectiveScale() or 1
    return parentScale * (self.scale or 1)
  end
  function frame:SetScale(value) self.scale = value end
  function frame:GetScale() return self.scale or 1 end
  function frame:SetAlpha(value) self.alpha = value end
  function frame:SetFrameStrata(value) self.strata = value end
  function frame:EnableMouse(value) self.mouse = value end
  function frame:SetSize(width, height) self.width, self.height = width, height end
  function frame:SetPoint(...) self.point = {...} end
  function frame:Show() self.shown = true end
  function frame:Hide() self.shown = false end
  function frame:IsShown() return self.shown == true end
  function frame:SetText(value) self.text = value end
  function frame:GetText() return self.text end
  function frame:SetEnabled(value) self.enabled = value == true end
  function frame:IsEnabled() return self.enabled ~= false end
  function frame:Click()
    if self.enabled ~= false and self.shown == true and self.onClick then self.onClick(self) end
  end
  function frame:CreateTexture()
    harness.textureCreateCount = harness.textureCreateCount + 1
    if harness.textureFailureAt > 0 and harness.textureCreateCount == harness.textureFailureAt then
      error("native texture construction failure")
    end
    local texture = { shown = false, parent = self, color = {0, 0, 0, 1} }
    function texture:SetSnapToPixelGrid(value) self.snap = value end
    function texture:SetTexelSnappingBias(value) self.bias = value end
    function texture:SetSize(width, height) self.width, self.height = width, height end
    function texture:SetPoint(...) self.point = {...} end
    function texture:SetColorTexture(r, g, b, a) self.color = {r, g, b, a} end
    function texture:SetTexture(path, wrapHorizontal, wrapVertical, filterMode)
      self.texture = path
      self.wrapHorizontal = wrapHorizontal
      self.wrapVertical = wrapVertical
      self.filterMode = filterMode
      -- Keep every argument, including omitted optional arguments, visible to
      -- the Python raster model.  The native client defaults are not inferred
      -- here: the recorded call is the contract under test.
      self.textureArgs = {
        textureAsset = path,
        wrapHorizontal = wrapHorizontal,
        wrapVertical = wrapVertical,
        filterMode = filterMode,
      }
    end
    function texture:SetTexCoord(left, right, top, bottom)
      self.texCoord = {left, right, top, bottom}
    end
    function texture:Show() self.shown = true end
    function texture:Hide() self.shown = false end
    table.insert(harness.textures, texture)
    return texture
  end
  table.insert(_events, frame)
  return frame
end

function _fire(event, ...)
  for _, frame in ipairs(_events) do
    if frame.events[event] and frame.onEvent then frame.onEvent(frame, event, ...) end
  end
end

function hooksecurefunc(target, name, callback)
  local original = target[name]
  target[name] = function(...)
    local results = { original(...) }
    callback(...)
    return unpack(results)
  end
end

C_Timer = { After = function(delay, fn) table.insert(_timers, { at = _now + delay, fn = fn }) end }

function _nextTimerAt()
  local earliest
  for _, timer in ipairs(_timers) do
    if not earliest or timer.at < earliest then earliest = timer.at end
  end
  return earliest
end

function _runTimers()
  local guard = 0
  while #_timers > 0 do
    local readyIndex, ready
    for i, timer in ipairs(_timers) do
      if timer.at <= _now and (not ready or timer.at < ready.at) then
        readyIndex, ready = i, timer
      end
    end
    if not ready then break end
    table.remove(_timers, readyIndex)
    ready.fn()
    guard = guard + 1
    if guard > 100000 then error("timer loop") end
  end
end

local function lookupAuction(itemID, commodity)
  for i = 1, #harness.auctions do
    local auction = harness.auctions[i]
    if auction.itemID == itemID and (commodity == nil or auction.isCommodity == commodity) then return auction end
  end
end

local function nativeClassID(itemID)
  if harness.missingClass and harness.missingClass[itemID] then return nil end
  local auction = lookupAuction(itemID)
  if auction then return auction.classID end
  return Enum.ItemClass.Tradegoods
end

local function nativeLevel(itemID)
  if not harness.keyWarm or not harness.keyWarm[itemID] then return 0 end
  local auction = lookupAuction(itemID)
  return auction and auction.itemLevel or 0
end

local function equipmentAuction(auction)
  return auction and not auction.isCommodity and
    (auction.classID == Enum.ItemClass.Weapon or auction.classID == Enum.ItemClass.Armor or auction.classID == Enum.ItemClass.Profession)
end

C_Item = {
  DoesItemExistByID = function(id) return id ~= 999999 end,
  GetItemInfoInstant = function(item)
    local itemID = type(item) == "number" and item or (type(item) == "table" and item.itemID)
    if type(itemID) ~= "number" then return nil end
    return itemID, "Item", "", "", 1, nativeClassID(itemID)
  end,
  RequestLoadItemDataByID = function(id)
    harness.requested[id] = true
    C_Timer.After(harness.metadataDelay or 0, function()
      if harness.metadataPending then harness.metadataPending[id] = nil end
      harness.keyWarm = harness.keyWarm or {}
      harness.keyWarm[id] = true
      _fire("ITEM_KEY_ITEM_INFO_RECEIVED", id)
    end)
  end,
}

-- Records what the addon pushes into Auctionator.
_lists = {}
Auctionator = { API = { v1 = {
  ConvertToSearchString = function(caller, term)
    return ('"%s";;;;;;;;;%s;;;;%s'):format(term.searchString, term.maxPrice / 10000, term.quantity)
  end,
  CreateShoppingList = function(caller, name, items) _lists[name] = items end,
} } }

local function keyValues(key)
  if type(key) ~= "table" then return nil end
  return key.itemID, key.itemLevel or 0, key.itemSuffix or 0, key.battlePetSpeciesID or 0
end

local function makeKey(itemID, itemLevel, itemSuffix, pet)
  return { itemID = itemID, itemLevel = itemLevel, itemSuffix = itemSuffix, battlePetSpeciesID = pet }
end

local function findAuction(itemID, commodity)
  return lookupAuction(itemID, commodity)
end

local function queryRows(itemID, commodity)
  local rows = {}
  for i = 1, #harness.auctions do
    local a = harness.auctions[i]
    if a.itemID == itemID and a.isCommodity == commodity then rows[#rows + 1] = a end
  end
  table.sort(rows, function(x, y)
    local xp = x.buyout
    local yp = y.buyout
    return xp < yp
  end)
  return rows
end

local function ownerList(a)
  local owners = a.owners or { a.owner or "Seller" }
  local result = {}
  for i, owner in ipairs(owners) do result[i] = owner end
  return result
end

local function appendSend(kind, itemID)
  harness.sendLog = harness.sendLog or {}
  table.insert(harness.sendLog, { at = _now, kind = kind, itemID = itemID })
end

local function recordQueryMethod(method, itemID, key)
  harness.queryMethods = harness.queryMethods or {}
  table.insert(harness.queryMethods, { method = method, itemID = itemID,
    itemLevel = key.itemLevel, itemSuffix = key.itemSuffix, battlePetSpeciesID = key.battlePetSpeciesID })
end

local function keysEqual(left, right)
  local li, ll, ls, lp = keyValues(left)
  local ri, rl, rs, rp = keyValues(right)
  return li and ri and li == ri and ll == rl and ls == rs and lp == rp
end

local function fireResults(kind, key, itemID)
  local event = harness.eventKind or "UPDATED"
  if harness.emitStale then
    _fire(kind == "commodity" and "COMMODITY_SEARCH_RESULTS_UPDATED" or "ITEM_SEARCH_RESULTS_UPDATED", kind == "commodity" and (itemID + 999999) or makeKey(itemID + 999999, 0, 0, 0))
  end
  if event ~= "NONE" then
    local name = (kind == "commodity" and "COMMODITY_SEARCH_RESULTS_" or "ITEM_SEARCH_RESULTS_") .. event
    if kind == "commodity" then _fire(name, itemID) else _fire(name, makeKey(key.itemID, key.itemLevel, key.itemSuffix, key.battlePetSpeciesID)) end
  end
end

local function emitResults(kind, key, itemID)
  local delay = harness.eventDelay or 0
  C_Timer.After(delay, function() fireResults(kind, key, itemID) end)
end

local function runSearchQuery(key, method)
  local itemID = keyValues(key)
  local commodity = findAuction(itemID, true) ~= nil
  local auction = findAuction(itemID, false)
  local valid = commodity and method == "SendSearchQuery" or
    not commodity and (not auction or not equipmentAuction(auction) and method == "SendSearchQuery" or
      equipmentAuction(auction) and method == "SendSellSearchQuery" and key.itemLevel == 0 and key.itemSuffix == 0 and key.battlePetSpeciesID == 0)
  harness.queryCalls = harness.queryCalls + 1
  harness.lastQuery = { key = key, itemID = itemID, commodity = commodity, valid = valid, loaded = 0 }
  local rows = queryRows(itemID, commodity)
  harness.lastQuery.loaded = valid and math.min(harness.pageSize or 50, #rows) or 0
  harness.lastQuery.full = not harness.forceIncomplete and harness.lastQuery.loaded >= #rows
  recordQueryMethod(method, itemID, key)
  appendSend("search", itemID)
  if valid and harness.eventBeforeBarriers then fireResults(commodity and "commodity" or "item", key, itemID) end
  _fire("AUCTION_HOUSE_THROTTLED_MESSAGE_SENT")
  _fire("AUCTION_HOUSE_THROTTLED_MESSAGE_RESPONSE_RECEIVED")
  if valid and not harness.eventBeforeBarriers then emitResults(commodity and "commodity" or "item", key, itemID) end
end

C_AuctionHouse = {
  IsThrottledMessageSystemReady = function()
    if harness.forceThrottle then return false end
    local count = 0
    for _, sent in ipairs(harness.sendLog or {}) do if _now - sent.at < 60 then count = count + 1 end end
    return count < 100
  end,
  MakeItemKey = function(itemID, itemLevel, itemSuffix, battlePetSpeciesID)
    local level = nativeLevel(itemID)
    if itemLevel ~= nil and itemLevel ~= 0 then level = itemLevel end
    return makeKey(itemID, level, itemSuffix or 0, battlePetSpeciesID or 0)
  end,
  GetItemKeyInfo = function(key, restrictQualityToFilter)
    local itemID = keyValues(key)
    if not itemID or (harness.metadataPending and harness.metadataPending[itemID]) then return nil end
    local a = findAuction(itemID, true) or findAuction(itemID, false)
    return { itemID = itemID, battlePetSpeciesID = key.battlePetSpeciesID or 0, itemName = a and a.name or ("Item " .. itemID),
      quality = a and a.quality or 1, iconFileID = 1, isPet = (key.battlePetSpeciesID or 0) > 0,
      isCommodity = a and a.isCommodity == true or false, isEquipment = equipmentAuction(a) == true }
  end,
  SendSellSearchQuery = function(key, sorts, separateOwnerItems)
    assert(type(key) == "table" and type(sorts) == "table" and type(separateOwnerItems) == "boolean", "documented SendSellSearchQuery signature")
    local itemID = keyValues(key)
    if findAuction(itemID, true) then
      recordQueryMethod("SendSellSearchQuery", itemID, key)
      harness.ignoredCommoditySellQueries = (harness.ignoredCommoditySellQueries or 0) + 1
      return
    end
    runSearchQuery(key, "SendSellSearchQuery")
  end,
  SendSearchQuery = function(key, sorts, separateOwnerItems, minLevelFilter, maxLevelFilter)
    assert(type(key) == "table" and type(sorts) == "table" and type(separateOwnerItems) == "boolean", "documented SendSearchQuery signature")
    runSearchQuery(key, "SendSearchQuery")
  end,
  RequestMoreCommoditySearchResults = function(itemID)
    assert(harness.lastQuery and harness.lastQuery.commodity and harness.lastQuery.itemID == itemID)
    local rows = queryRows(itemID, true)
    harness.lastQuery.loaded = math.min(harness.lastQuery.loaded + (harness.pageSize or 50), #rows)
    harness.lastQuery.full = not harness.forceIncomplete and harness.lastQuery.loaded >= #rows
    harness.queryCalls = harness.queryCalls + 1
    appendSend("commodity_page", itemID)
    if harness.eventBeforeBarriers then fireResults("commodity", harness.lastQuery.key, itemID) end
    _fire("AUCTION_HOUSE_THROTTLED_MESSAGE_SENT")
    _fire("AUCTION_HOUSE_THROTTLED_MESSAGE_RESPONSE_RECEIVED")
    if not harness.eventBeforeBarriers then emitResults("commodity", harness.lastQuery.key, itemID) end
    return harness.lastQuery.full
  end,
  RequestMoreItemSearchResults = function(key)
    local itemID = keyValues(key)
    assert(harness.lastQuery and not harness.lastQuery.commodity and harness.lastQuery.itemID == itemID)
    local rows = queryRows(itemID, false)
    harness.lastQuery.loaded = math.min(harness.lastQuery.loaded + (harness.pageSize or 50), #rows)
    harness.lastQuery.full = not harness.forceIncomplete and harness.lastQuery.loaded >= #rows
    harness.queryCalls = harness.queryCalls + 1
    appendSend("item_page", itemID)
    if harness.eventBeforeBarriers then fireResults("item", key, itemID) end
    _fire("AUCTION_HOUSE_THROTTLED_MESSAGE_SENT")
    _fire("AUCTION_HOUSE_THROTTLED_MESSAGE_RESPONSE_RECEIVED")
    if not harness.eventBeforeBarriers then emitResults("item", key, itemID) end
    return harness.lastQuery.full
  end,
  HasFullCommoditySearchResults = function(itemID)
    return harness.lastQuery and harness.lastQuery.commodity and harness.lastQuery.itemID == itemID and harness.lastQuery.full or false
  end,
  HasFullItemSearchResults = function(key)
    local itemID = keyValues(key)
    return harness.lastQuery and not harness.lastQuery.commodity and harness.lastQuery.itemID == itemID and harness.lastQuery.full or false
  end,
  HasSearchResults = function(key)
    local itemID, itemLevel, itemSuffix, pet = keyValues(key)
    local current = harness.lastQuery
    return current and current.itemID == itemID and current.key.itemLevel == itemLevel and
      current.key.itemSuffix == itemSuffix and current.key.battlePetSpeciesID == pet or false
  end,
  GetCommoditySearchResultsQuantity = function(itemID)
    if not harness.lastQuery or not harness.lastQuery.commodity or harness.lastQuery.itemID ~= itemID then return 0 end
    local total = 0
    for index, auction in ipairs(queryRows(itemID, true)) do
      if index > harness.lastQuery.loaded then break end
      total = total + auction.count
    end
    return total
  end,
  GetItemSearchResultsQuantity = function(key)
    local itemID = keyValues(key)
    if not harness.lastQuery or harness.lastQuery.commodity or harness.lastQuery.itemID ~= itemID then return 0 end
    local total = 0
    for index, auction in ipairs(queryRows(itemID, false)) do
      if index > harness.lastQuery.loaded then break end
      total = total + auction.count
    end
    return total
  end,
  GetNumItemSearchResults = function(key)
    local itemID = keyValues(key); if not harness.lastQuery or harness.lastQuery.commodity or harness.lastQuery.itemID ~= itemID then return 0 end
    return math.min(harness.lastQuery.loaded, #queryRows(itemID, false))
  end,
  GetItemSearchResultInfo = function(key, index)
    local itemID = keyValues(key); local rows = queryRows(itemID, false)
    if not harness.lastQuery or not harness.lastQuery.valid or harness.lastQuery.commodity or harness.lastQuery.itemID ~= itemID or
        not keysEqual(key, harness.lastQuery.key) or index > harness.lastQuery.loaded or
        (harness.missingResults and harness.missingResults[index]) then return nil end
    local a = rows[index]; if not a then return nil end
    local itemKey = makeKey(a.itemID, a.itemLevel or 0, a.itemSuffix or 0, a.battlePetSpeciesID or 0)
    return { itemKey = itemKey, owners = ownerList(a), totalNumberOfOwners = a.totalOwners or #(a.owners or { a.owner or "Seller" }),
      timeLeft = a.timeLeft, auctionID = a.auctionID, quantity = a.count, itemLink = a.link,
      containsOwnerItem = a.containsOwnerItem == true, containsAccountItem = a.containsAccountItem == true,
      containsSocketedItem = false, minBid = a.minBid > 0 and a.minBid or nil, bidAmount = a.bid > 0 and a.bid or nil,
      buyoutAmount = a.buyout > 0 and a.buyout or nil, timeLeftSeconds = a.timeLeftSeconds }
  end,
  GetNumCommoditySearchResults = function(itemID)
    if not harness.lastQuery or not harness.lastQuery.commodity or harness.lastQuery.itemID ~= itemID then return 0 end
    return math.min(harness.lastQuery.loaded, #queryRows(itemID, true))
  end,
  GetCommoditySearchResultInfo = function(itemID, index)
    if not harness.lastQuery or not harness.lastQuery.commodity or harness.lastQuery.itemID ~= itemID or index > harness.lastQuery.loaded or
        (harness.missingResults and harness.missingResults[index]) then return nil end
    local a = queryRows(itemID, true)[index]; if not a then return nil end
    return { itemID = a.itemID, quantity = a.count, unitPrice = a.buyout, auctionID = a.auctionID,
      owners = ownerList(a), totalNumberOfOwners = a.totalOwners or #(a.owners or { a.owner or "Seller" }),
      timeLeftSeconds = a.timeLeftSeconds, numOwnerItems = a.numOwnerItems or 0,
      containsOwnerItem = a.containsOwnerItem == true, containsAccountItem = a.containsAccountItem == true }
  end,
  QueryOwnedAuctions = function(sorts)
    assert(type(sorts) == "table" and type(sorts[1]) == "table" and
      type(sorts[1].sortOrder) == "number" and type(sorts[1].reverseSort) == "boolean",
      "documented QueryOwnedAuctions signature")
    harness.ownedQueries = harness.ownedQueries + 1
    appendSend("owned", 0)
    _fire("AUCTION_HOUSE_THROTTLED_MESSAGE_SENT")
    _fire("AUCTION_HOUSE_THROTTLED_MESSAGE_RESPONSE_RECEIVED")
    C_Timer.After(harness.ownedDelay or 0, function()
      if harness.emitOwnedEvent ~= false then _fire("OWNED_AUCTIONS_UPDATED") end
    end)
  end,
  HasFullOwnedAuctionResults = function() return harness.ownedFull ~= false end,
  GetNumOwnedAuctions = function() return #(harness.owned or {}) end,
  GetOwnedAuctionInfo = function(index)
    local a = (harness.owned or {})[index]; if not a then return nil end
    return { auctionID = a.auctionID, itemKey = makeKey(a.itemID, a.itemLevel or 0, a.itemSuffix or 0, a.battlePetSpeciesID or 0),
      itemLink = a.link, status = a.status == "sold" and Enum.AuctionStatus.Sold or Enum.AuctionStatus.Active,
      quantity = a.count, timeLeftSeconds = a.timeLeftSeconds, timeLeft = a.timeLeft,
      bidAmount = a.bid > 0 and a.bid or nil, buyoutAmount = a.buyout > 0 and a.buyout or nil }
  end,
  GetTimeLeftBandInfo = function(band) return band * 3600, band * 3600 + 3600 end,
}

function _serialize(name, value)
  local out = {}
  local function emit(v, indent)
    local t = type(v)
    if t == "table" then
      table.insert(out, "{\n")
      for k, child in pairs(v) do
        table.insert(out, indent .. "\t[" .. (type(k) == "string" and string.format("%q", k) or tostring(k)) .. "] = ")
        emit(child, indent .. "\t")
        table.insert(out, ",\n")
      end
      table.insert(out, indent .. "}")
    elseif t == "string" then
      table.insert(out, string.format("%q", v))
    else
      table.insert(out, tostring(v))
    end
  end
  table.insert(out, name .. " = ")
  emit(value, "")
  table.insert(out, "\n")
  return table.concat(out)
end

function ReloadUI()
  harness.reloadCalls = (harness.reloadCalls or 0) + 1
end
"""


@dataclass
class Auction:
    itemID: int
    name: str
    count: int
    buyout: int
    link: str = ""
    minBid: int = 0
    bid: int = 0
    owner: str = "Seller"
    timeLeft: int = 3
    quality: int = 1
    level: int = 1
    hasAllInfo: bool = True
    isCommodity: bool = False
    itemLevel: int = 0
    itemSuffix: int = 0
    classID: int | None = 7
    battlePetSpeciesID: int = 0
    bonusIDs: list[int] = field(default_factory=list)
    owners: list[str] = field(default_factory=list)
    hiddenOwners: bool = False
    totalOwners: int = 0
    containsOwnerItem: bool = False
    containsAccountItem: bool = False
    numOwnerItems: int = 0
    timeLeftSeconds: int | None = None
    auctionID: int | None = -1
    status: str = "active"

    def __post_init__(self) -> None:
        global _NEXT_AUCTION_ID
        if self.auctionID == -1:
            self.auctionID = _NEXT_AUCTION_ID
            _NEXT_AUCTION_ID += 1
        if not self.link:
            bonuses = ":".join(str(value) for value in self.bonusIDs)
            count = len(self.bonusIDs)
            fields = [
                str(self.itemID),
                "0",
                "0",
                "0",
                "0",
                "0",
                str(self.itemSuffix),
                "0",
                str(self.level),
                "0",
                "0",
                "0",
                str(count),
            ]
            if bonuses:
                fields.append(bonuses)
            self.link = "|Hitem:" + ":".join(fields) + f"|h[{self.name}]|h"
        if not self.owners and not self.hiddenOwners:
            self.owners = [self.owner]
        if not self.totalOwners and not self.hiddenOwners:
            self.totalOwners = len(self.owners)


@dataclass
class WowClient:
    faction: str = "Horde"
    realm: str = "Normal"
    zone: str = "Orgrimmar"
    subzone: str = ""
    auctions: list[Auction] = field(default_factory=list)
    current_region: int | None = 1
    current_region_name: str | None = "US"
    realm_info: bool = False
    game_rules: bool = True
    presentation_width: int = 1920
    presentation_height: int = 1080
    root_ui_scale: float = 1.0
    root_width: float | None = None
    root_height: float | None = None
    root_effective_scale: float | None = None
    position: tuple[float, float, float, int] = (100.25, 200.5, 30.75, 1)
    facing: float = 1.25
    speed: float = 0.0
    speed_run: float = 7.0
    speed_flight: float = 7.0
    speed_swim: float = 4.7222218513489
    ctm_mode: str = "false"
    ctm_missing: bool = False
    ground_modes: dict[str, str] = field(
        default_factory=lambda: {
            "flying": "false",
            "falling": "false",
            "swimming": "false",
            "submerged": "false",
            "mounted": "false",
            "taxi": "false",
        }
    )
    combat: bool = False
    dead_or_ghost: bool = False
    bindings: dict[str, str] = field(
        default_factory=lambda: {
            "MOVEFORWARD": "W",
            "MOVEBACKWARD": "S",
            "STRAFELEFT": "A",
            "STRAFERIGHT": "D",
            "TURNLEFT": "Q",
        }
    )
    initial_savedvars: dict | None = None

    def __post_init__(self) -> None:
        if self.presentation_width != 1920 or self.presentation_height != 1080:
            raise ValueError("the harness models only the pinned 1920x1080 presentation")
        if self.root_ui_scale <= 0:
            raise ValueError("root_ui_scale must be positive")
        if self.root_effective_scale is None:
            self.root_effective_scale = self.root_ui_scale
        if self.root_height is None:
            self.root_height = 768 / self.root_ui_scale
        if self.root_width is None:
            self.root_width = (1920 / 1080) * self.root_height
        self.lua = lua51.LuaRuntime(unpack_returned_tuples=True, encoding="latin-1")
        self.state = self.lua.table_from(
            {
                "faction": self.faction,
                "realm": self.realm,
                "zone": self.zone,
                "subzone": self.subzone,
                "region": self.current_region,
                "regionName": self.current_region_name,
                "realmInfo": self.realm_info,
                "gameRules": self.game_rules,
                "rootWidth": self.root_width,
                "rootHeight": self.root_height,
                "rootEffectiveScale": self.root_effective_scale,
                "positionX": self.position[0],
                "positionY": self.position[1],
                "positionZ": self.position[2],
                "positionInstance": self.position[3],
                "facing": self.facing,
                "speed": self.speed,
                "speedRun": self.speed_run,
                "speedFlight": self.speed_flight,
                "speedSwim": self.speed_swim,
                "speedTuple": self.lua.table_from(
                    {1: self.speed, 2: self.speed_run, 3: self.speed_flight, 4: self.speed_swim}
                ),
                "ctmMode": self.ctm_mode,
                "ctmMissing": self.ctm_missing,
                "groundModes": self._to_lua(self.ground_modes),
                "groundArgCounts": self.lua.table(),
                "combat": self.combat,
                "deadOrGhost": self.dead_or_ghost,
                "bindings": self.lua.table(),
                "requested": self.lua.table(),
                "queryCalls": 0,
                "queryMethods": self.lua.table(),
                "ignoredCommoditySellQueries": 0,
                "ownedQueries": 0,
                "auctions": self.lua.table(),
                "owned": self.lua.table(),
                "ownedFull": True,
                "emitOwnedEvent": True,
                "sendLog": self.lua.table(),
                "missingResults": self.lua.table(),
                "keyWarm": self.lua.table(),
                "missingClass": self.lua.table(),
                "textures": self.lua.table(),
                "chatEdit": self.lua.table_from({"shown": False, "focused": False, "text": ""}),
                "luaHeapAvailable": True,
                "luaHeapValue": 512,
                "luaHeapValues": self.lua.table(),
                "luaHeapIndex": 0,
                "gcCalls": 0,
                "gcMutations": 0,
                "reloadCalls": 0,
                "textureCreateCount": 0,
                "textureFailureAt": 0,
            }
        )
        for action, key in self.bindings.items():
            self.state.bindings[action] = key
        self.lua.execute("return function(...) " + STUBS + " end")(self.state)
        self._install_codec()
        self.ns = self.lua.table()
        if self.initial_savedvars is not None:
            self.lua.globals().CrowleyDB = self._to_lua(self.initial_savedvars)
        self._load_addon()

    def _install_codec(self) -> None:
        # The runtime maps Lua byte strings to latin-1 str, so convert at the boundary.
        def raw(s):
            return s.encode("latin-1") if isinstance(s, str) else s

        def compress(s, method):
            assert method == 0  # Enum.CompressionMethod.Deflate: raw deflate
            compressor = zlib.compressobj(wbits=-zlib.MAX_WBITS)
            return compressor.compress(raw(s)) + compressor.flush()

        def to_lua(value):
            if isinstance(value, dict):
                table = self.lua.table()
                for key, child in value.items():
                    table[key] = to_lua(child)
                return table
            if isinstance(value, list):
                table = self.lua.table()
                for index, child in enumerate(value, start=1):
                    table[index] = to_lua(child)
                return table
            return value

        def from_lua(value):
            if hasattr(value, "items"):
                pairs = list(value.items())
                if not pairs:
                    # C_EncodingUtil.SerializeJSON follows the native WoW
                    # table encoder: an empty Lua table is an array, while a
                    # non-empty keyed table is an object.
                    return []
                if all(isinstance(key, (int, float)) for key, _ in pairs):
                    return [from_lua(child) for _, child in sorted(pairs)]
                return {str(key): from_lua(child) for key, child in pairs}
            return value

        g = self.lua.globals()
        g.C_EncodingUtil = self.lua.table_from(
            {
                "CompressString": compress,
                "EncodeBase64": lambda b: base64.b64encode(raw(b)).decode(),
                "DeserializeJSON": lambda source: to_lua(json.loads(source)),
                "SerializeJSON": lambda value: json.dumps(
                    from_lua(value), sort_keys=True, separators=(",", ":")
                ),
            }
        )

    def _load_addon(self) -> None:
        # Load order mirrors the client: dependency Crowley_Data first, then Crowley's TOC.
        self.run_file(ADDONS / "Crowley_Data" / "Data.lua")
        for line in (ADDONS / "Crowley" / "Crowley.toc").read_text().splitlines():
            if line.endswith(".lua"):
                self.run_file(ADDONS / "Crowley" / line)

    def inject_saved_variables(self, value: dict) -> None:
        """Inject SavedVariables after file execution and before ADDON_LOADED."""

        self.lua.globals().CrowleyDB = self._to_lua(value)

    def run_file(self, path: Path) -> None:
        chunk = self.lua.globals().loadstring(path.read_text(), "@" + path.name)
        if chunk is None:
            raise SyntaxError(f"failed to load {path}")
        chunk("Crowley", self.ns)

    def set_auctions(self, auctions: list[Auction]) -> None:
        table = self.lua.table()
        for i, auction in enumerate(auctions, start=1):
            table[i] = self._to_lua(auction.__dict__)
        self.state.auctions = table

    def set_source_incomplete(self, incomplete: bool = True) -> None:
        self.state.forceIncomplete = incomplete

    def set_missing_results(self, indices: list[int]) -> None:
        self.state.missingResults = self._to_lua({index: True for index in indices})

    def set_house(self, *, faction: str | None = None, realm: str | None = None) -> None:
        if faction is not None:
            self.state.faction = faction
        if realm is not None:
            self.state.realm = realm

    def set_region(self, *, region: int | None = None, name: str | None = None) -> None:
        self.state.region = region
        self.state.regionName = name

    def set_owned(self, auctions: list[Auction], *, complete: bool = True) -> None:
        table = self.lua.table()
        for i, auction in enumerate(auctions, start=1):
            table[i] = self._to_lua(auction.__dict__)
        self.state.owned = table
        self.state.ownedFull = complete

    def set_metadata_pending(self, item_ids: list[int]) -> None:
        self.state.metadataPending = self._to_lua({item_id: True for item_id in item_ids})
        if self.state.metadataDelay:
            self.state.fastCanonical = False

    def set_key_warm(self, item_ids: list[int]) -> None:
        self.state.keyWarm = self._to_lua({item_id: True for item_id in item_ids})

    def set_class_unavailable(self, item_ids: list[int]) -> None:
        self.state.missingClass = self._to_lua({item_id: True for item_id in item_ids})

    def set_event_behavior(
        self, *, kind: str = "UPDATED", delay: int = 0, stale: bool = False, before_barriers: bool = False
    ) -> None:
        self.state.eventKind = kind
        self.state.eventDelay = delay
        self.state.emitStale = stale
        self.state.eventBeforeBarriers = before_barriers
        if delay or kind != "UPDATED" or stale or before_barriers:
            self.state.fastCanonical = False

    def external_search(self, item_id: int) -> None:
        key = self.lua.globals().C_AuctionHouse.MakeItemKey(item_id, 0, 0, 0)
        sorts = self.lua.table()
        sorts[1] = self._to_lua({"sortOrder": 1, "reverseSort": False})
        self.lua.globals().C_AuctionHouse.SendSearchQuery(key, sorts, False, 0, 0)

    def set_owned_behavior(self, *, complete: bool = True, emit: bool = True, delay: int = 0) -> None:
        self.state.ownedFull = complete
        self.state.emitOwnedEvent = emit
        self.state.ownedDelay = delay
        if not complete or not emit or delay:
            self.state.fastCanonical = False

    def set_throttled(self, throttled: bool = True) -> None:
        self.state.forceThrottle = throttled
        if throttled:
            self.state.fastCanonical = False

    def set_lua_heap(
        self, *, available: bool = True, values: list[float] | None = None, value: float = 512
    ) -> None:
        self.state.luaHeapAvailable = available
        self.state.luaHeapValue = value
        self.state.luaHeapValues = self._to_lua(values or [])
        self.state.luaHeapIndex = 0

    def set_motion(
        self,
        *,
        position: tuple[float, float, float, int] | None = None,
        facing: float | None = None,
        speed: float | None = None,
        combat: bool | None = None,
        dead_or_ghost: bool | None = None,
        bindings: dict[str, str] | None = None,
    ) -> None:
        """Mutate the native movement APIs exposed by this client fixture."""

        if position is not None:
            self.state.positionX, self.state.positionY, self.state.positionZ, self.state.positionInstance = (
                position
            )
        if facing is not None:
            self.state.facing = facing
        if speed is not None:
            self.state.speed = speed
            self.state.speedTuple[1] = speed
        if combat is not None:
            self.state.combat = combat
        if dead_or_ghost is not None:
            self.state.deadOrGhost = dead_or_ghost
        if bindings is not None:
            self.state.bindings = self._to_lua(bindings)

    def probe(self) -> dict:
        self.ns.Probe()
        return self._json_table(self.lua.globals().CrowleyDB.probe)

    @property
    def gc_calls(self) -> int:
        return int(self.state.gcCalls or 0)

    @property
    def gc_mutations(self) -> int:
        return int(self.state.gcMutations or 0)

    @property
    def send_log(self) -> list[dict]:
        return [dict(entry.items()) for entry in self.state.sendLog.values()]

    @property
    def query_methods(self) -> list[dict]:
        return [dict(entry.items()) for entry in self.state.queryMethods.values()]

    @property
    def ignored_commodity_sell_queries(self) -> int:
        return self.state.ignoredCommoditySellQueries

    def _json_table(self, value) -> dict | None:
        if value is None:
            return None
        return json.loads(self.lua.globals().C_EncodingUtil.SerializeJSON(value))

    @property
    def query_trace(self) -> dict | None:
        return self._json_table(self.lua.globals().CrowleyDB.lastQueryTrace)

    @property
    def active_query_trace(self) -> dict | None:
        return self._json_table(self.lua.globals().CrowleyDB.activeQueryTrace)

    def set_readiness_api(self, name: str, mode: str) -> None:
        if mode == "absent":
            self.lua.globals().C_AuctionHouse[name] = None
        elif mode == "throwing":
            self.lua.globals().C_AuctionHouse[name] = self.lua.eval(
                "function() error('diagnostic test error') end"
            )
        else:
            raise ValueError(f"unknown readiness API mode: {mode}")

    def set_texture_failure(self, index: int | None) -> None:
        """Fail the actual CreateTexture callback at a deterministic ordinal."""

        self.state.textureCreateCount = 0
        self.state.textureFailureAt = int(index or 0)

    @property
    def visible_native_textures(self) -> list[bool]:
        return [bool(texture.shown) for texture in self.state.textures.values()]

    def set_plan(self, item_ids: list[int]) -> None:
        body = {
            "schemaVersion": 2,
            "id": "first-run",
            "revision": 1,
            "catalogHash": "a" * 64,
            # Keep the fixture on the measured Forever client.  Deliberately
            # short plans remain negative fixtures for the production
            # canonical-plan gate; the old false build hid that gate entirely.
            "targetClientBuild": "1.60.1.70450",
            "cadenceSeconds": 900,
            "initialPriceLevels": 20,
            "itemIDs": sorted(item_ids),
            "pools": {"core": sorted(item_ids), "discovery": []},
        }
        plan_json = json.dumps(body, sort_keys=True, separators=(",", ":"))
        plan = {**body, "planHash": hashlib.sha256(plan_json.encode()).hexdigest(), "planJSON": plan_json}
        self.lua.globals().CROWLEY_DATA.scanPlan = self._to_lua(plan)

    def set_canonical_plan(self) -> None:
        """Load the exact shipped 428-ID plan into the native fixture."""

        self.lua.globals().CROWLEY_DATA.scanPlan = self._to_lua(load_catalog().scan_plan())
        # This is a harness clock convenience only.  It advances to the next
        # real timer deadline after the current callbacks drain, while the
        # production scanner still enforces its 100/60s send window.  Tests
        # that exercise late or out-of-order events disable it through one of
        # the behavior setters above.
        self.state.fastCanonical = True

    def focus_item(self, item_id: int) -> None:
        """Rotate the canonical order so an adversarial fixture starts here."""

        ids = load_catalog().scan_plan()["itemIDs"]
        index = ids.index(item_id)
        previous = ids[index - 1] if index else ids[-1]
        db = self.lua.globals().CrowleyDB
        db.cursorItemID = previous
        db.cursorPlanHash = load_catalog().scan_plan()["planHash"]

    def _to_lua(self, value):
        if isinstance(value, dict):
            table = self.lua.table()
            for key, child in value.items():
                table[key] = self._to_lua(child)
            return table
        if isinstance(value, list):
            table = self.lua.table()
            for index, child in enumerate(value, start=1):
                table[index] = self._to_lua(child)
            return table
        return value

    def fire(self, event: str, *args) -> None:
        self.lua.globals()._fire(event, *args)

    def set_chat_edit(self, *, active: bool, focused: bool, text: str = "") -> None:
        edit = self.state.chatEdit
        edit.shown, edit.focused, edit.text = active, focused, text

    def set_chat_edit_bytes(self, *, active: bool, focused: bool, text: bytes = b"") -> None:
        """Set the edit box with the exact byte sequence Lua's ``#`` observes."""

        self.set_chat_edit(active=active, focused=focused, text=text.decode("latin-1"))

    def publish_agent(self) -> dict:
        return self._json_table(self.ns.Agent.Publish())

    def snapshot_agent(self) -> dict:
        return self._json_table(self.ns.Agent.Snapshot())

    def update_agent(self, seconds: float = 1.0) -> None:
        surface = self.ns.Agent.Surface()
        surface.onUpdate(surface, seconds)

    @property
    def agent_frame(self) -> bytes:
        value = self.ns.Agent.FrameBytes()
        return value.encode("latin-1") if isinstance(value, str) else bytes(value)

    @property
    def texture_count(self) -> int:
        return len(list(self.state.textures.values()))

    @staticmethod
    def _byte_atlas() -> Image.Image:
        global _BYTE_ATLAS
        if _BYTE_ATLAS is None:
            _BYTE_ATLAS = Image.open(_BYTE_ATLAS_PATH).convert("RGBA")
            if _BYTE_ATLAS.size != (16, 512):
                raise AssertionError("ByteAtlas.tga has an unexpected size")
            if any(_BYTE_ATLAS.getpixel((x, y))[3] != 255 for y in range(512) for x in range(16)):
                raise AssertionError("ByteAtlas.tga contains transparent glyph pixels")
        return _BYTE_ATLAS

    @staticmethod
    def _point_component(value, index: int) -> float:
        if value is None:
            raise AssertionError("native texture/frame point is missing")
        result = value[index]
        if (
            isinstance(result, bool)
            or not isinstance(result, (int, float))
            or not math.isfinite(float(result))
        ):
            raise AssertionError("native texture/frame point is malformed")
        return float(result)

    @staticmethod
    def _assert_frame_point(point, *, name: str, relative_name: str) -> None:
        if point is None or point[1] != "TOPLEFT" or point[3] != "TOPLEFT":
            raise AssertionError(f"native {name} is not anchored TOPLEFT to TOPLEFT")
        if getattr(point[2], "name", None) != relative_name:
            raise AssertionError(f"native {name} has an unexpected relative frame")
        for index in (4, 5):
            value = point[index]
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
            ):
                raise AssertionError(f"native {name} offset is malformed")

    @classmethod
    def _sample_bilinear(cls, atlas: Image.Image, u: float, v: float) -> tuple[int, int, int]:
        """Sample the recorded atlas UV using the native linear texture model."""

        width, height = atlas.size
        if not 0 <= u <= 1 or not 0 <= v <= 1:
            raise AssertionError("native atlas UV is outside 0..1")
        source_x = u * width - 0.5
        source_y = v * height - 0.5
        x0 = max(0, min(width - 1, math.floor(source_x)))
        y0 = max(0, min(height - 1, math.floor(source_y)))
        x1 = max(0, min(width - 1, x0 + 1))
        y1 = max(0, min(height - 1, y0 + 1))
        fx = source_x - math.floor(source_x)
        fy = source_y - math.floor(source_y)
        top_left = atlas.getpixel((x0, y0))
        top_right = atlas.getpixel((x1, y0))
        bottom_left = atlas.getpixel((x0, y1))
        bottom_right = atlas.getpixel((x1, y1))
        return tuple(
            round(
                top_left[channel] * (1 - fx) * (1 - fy)
                + top_right[channel] * fx * (1 - fy)
                + bottom_left[channel] * (1 - fx) * fy
                + bottom_right[channel] * fx * fy
            )
            for channel in range(3)
        )

    @staticmethod
    def _sample_nearest(atlas: Image.Image, u: float, v: float) -> tuple[int, int, int]:
        """Sample the recorded atlas UV using the native nearest model."""

        width, height = atlas.size
        if not 0 <= u <= 1 or not 0 <= v <= 1:
            raise AssertionError("native atlas UV is outside 0..1")
        x = max(0, min(width - 1, math.floor(u * width)))
        y = max(0, min(height - 1, math.floor(v * height)))
        pixel = atlas.getpixel((x, y))
        return pixel[:3]

    def render_agent_screenshot(self) -> Image.Image:
        """Rasterize the actual recorded frame, texture rectangles, and atlas UVs."""

        atlas = self._byte_atlas()
        screenshot = Image.new("RGB", (self.presentation_width, self.presentation_height), (17, 17, 17))
        surface = self.ns.Agent.Surface()
        if surface is None or not surface.shown:
            raise AssertionError("native telemetry surface is not shown")
        root_factor = float(self.root_height) * float(self.root_effective_scale) / self.presentation_height
        if root_factor <= 0 or not math.isfinite(root_factor):
            raise AssertionError("native root geometry is invalid")
        surface_point = surface.point
        self._assert_frame_point(surface_point, name="telemetry surface", relative_name="UIParent")
        if (
            abs(self._point_component(surface_point, 4)) > 1e-6
            or abs(self._point_component(surface_point, 5)) > 1e-6
        ):
            raise AssertionError("native telemetry surface must have a zero UIParent offset")
        if surface.width != 336 or surface.height != 304:
            raise AssertionError("native telemetry surface does not include the pinned crop offset")
        surface_scale = float(surface.scale)
        if not math.isfinite(surface_scale) or surface_scale <= 0:
            raise AssertionError("native telemetry surface scale is invalid")
        if abs(surface.GetEffectiveScale(surface) - surface_scale) > 1e-6:
            raise AssertionError("native telemetry surface effective scale ignores its parent incorrectly")
        # The harness models anchored-frame coordinates in the frame's own
        # effective scale.  The production surface deliberately uses a zero
        # UIParent offset, removing the unresolved client offset convention.
        surface_x = self._point_component(surface_point, 4) * surface_scale / root_factor
        surface_y = -self._point_component(surface_point, 5) * surface_scale / root_factor
        for texture in self.state.textures.values():
            texture_args = texture.textureArgs
            if (
                not texture.shown
                or texture_args is None
                or texture_args.textureAsset != "Interface\\AddOns\\Crowley\\Textures\\ByteAtlas"
            ):
                raise AssertionError("native glyph texture is missing its atlas")
            if (
                texture_args.wrapHorizontal != "CLAMP"
                or texture_args.wrapVertical != "CLAMP"
                or texture_args.filterMode not in {"NEAREST", "LINEAR"}
            ):
                raise AssertionError("native glyph texture has an unsupported sampling contract")
            filter_mode = texture_args.filterMode
            point = texture.point
            self._assert_frame_point(point, name="glyph texture", relative_name="CrowleyAgentSurface")
            if texture.snap is not True or texture.bias != 0.5:
                raise AssertionError("native glyph texture is missing the pinned pixel snapping")
            local_x = self._point_component(point, 4) * surface_scale / root_factor
            local_y = -self._point_component(point, 5) * surface_scale / root_factor
            width = float(texture.width) * surface_scale / root_factor
            height = float(texture.height) * surface_scale / root_factor
            if not math.isfinite(width) or not math.isfinite(height) or width <= 0 or height <= 0:
                raise AssertionError("native glyph texture geometry is invalid")
            left = surface_x + local_x
            top = surface_y + local_y
            x0 = math.floor(left + 0.5)
            y0 = math.floor(top + 0.5)
            x1 = math.floor(left + width + 0.5)
            y1 = math.floor(top + height + 0.5)
            if x1 <= x0 or y1 <= y0:
                raise AssertionError("native glyph texture has no rasterized pixels")
            uv = texture.texCoord
            u0 = self._point_component(uv, 1)
            u1 = self._point_component(uv, 2)
            v0 = self._point_component(uv, 3)
            v1 = self._point_component(uv, 4)
            if not (0 <= u0 < u1 <= 1 and 0 <= v0 < v1 <= 1):
                raise AssertionError("native glyph texture has unsafe atlas UVs")
            pixels = screenshot.load()
            for dy in range(y1 - y0):
                v = v0 + (dy + 0.5) / (y1 - y0) * (v1 - v0)
                for dx in range(x1 - x0):
                    u = u0 + (dx + 0.5) / (x1 - x0) * (u1 - u0)
                    pixel_x, pixel_y = x0 + dx, y0 + dy
                    if 0 <= pixel_x < self.presentation_width and 0 <= pixel_y < self.presentation_height:
                        if filter_mode == "NEAREST":
                            sample = self._sample_nearest(atlas, u, v)
                        else:
                            sample = self._sample_bilinear(atlas, u, v)
                        pixels[pixel_x, pixel_y] = sample
        return screenshot

    def assert_native_geometry(self) -> None:
        """Assert the requested effective scale for a valid native geometry proof."""

        surface = self.ns.Agent.Surface()
        root_factor = float(self.root_height) * float(self.root_effective_scale) / self.presentation_height
        if surface is None or not surface.shown:
            raise AssertionError("native telemetry surface is not shown")
        if not math.isfinite(float(surface.scale)) or float(surface.scale) <= 0:
            raise AssertionError("native telemetry surface scale is invalid")
        if abs(float(surface.scale) - root_factor) > 1e-6:
            raise AssertionError("native telemetry surface scale does not match the requested native factor")

    def render_agent_capture(self) -> Image.Image:
        """Return the pinned crop from an actual full-presentation raster."""

        screenshot = self.render_agent_screenshot()
        return screenshot.crop((80, 48, 80 + 256, 48 + 256))

    def run_timers(self) -> None:
        g = self.lua.globals()
        if not self.state.fastCanonical:
            g._runTimers()
            return
        before = len(list(g.CrowleyDB.scans.items())) if g.CrowleyDB else 0
        for _ in range(2000):
            g._runTimers()
            after = len(list(g.CrowleyDB.scans.items())) if g.CrowleyDB else 0
            if after > before:
                return
            deadline = g._nextTimerAt()
            if deadline is None:
                return
            g._now = deadline

    def advance(self, seconds: int) -> None:
        g = self.lua.globals()
        g._now = g._now + seconds

    def advance_with_timers(self, seconds: int) -> None:
        """Advance the fake clock while dispatching timers at their deadlines.

        ``advance`` intentionally leaves due callbacks queued so tests can model a
        late event.  Lifecycle tests that need real deadline ordering should use
        this helper instead of jumping straight to the target timestamp.
        """
        g = self.lua.globals()
        target = g._now + seconds
        while True:
            deadline = g._nextTimerAt()
            if deadline is None or deadline > target:
                break
            g._now = deadline
            g._runTimers()
        g._now = target
        g._runTimers()

    def slash(self, msg: str) -> None:
        self.lua.globals().SlashCmdList.CROWLEY(msg)

    @property
    def shopping_lists(self) -> dict[str, list[str]]:
        return {k: list(v.values()) for k, v in self.lua.globals()._lists.items()}

    @property
    def chat(self) -> list[str]:
        return list(self.lua.globals()._chat.values())

    def saved_variables(self) -> bytes:
        g = self.lua.globals()
        return g._serialize("CrowleyDB", g.CrowleyDB).encode("latin-1")

    def login(self) -> None:
        self.fire("ADDON_LOADED", "Crowley")

    @property
    def reload_calls(self) -> int:
        return int(self.state.reloadCalls or 0)

    def click_native(self, role: str) -> None:
        names = {
            "construct": "CrowleyNativeConstructionConstruct",
            "restore": "CrowleyNativeConstructionRestore",
        }
        if role not in names:
            raise ValueError(f"unknown native construction control {role}")
        control = self.lua.globals()[names[role]]
        if control is None:
            raise AssertionError(f"native construction {role} control is unavailable")
        control.Click(control)
