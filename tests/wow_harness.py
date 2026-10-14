"""Runs the real addon Lua under Lua 5.1 (WoW's version) against a fake WoW client API."""

from __future__ import annotations

import base64
import hashlib
import json
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from lupa import lua51

ADDONS = Path(__file__).resolve().parents[1] / "addon"
_NEXT_AUCTION_ID = 1

STUBS = r"""
local harness = ...
_events = {}
_timers = {}
_chat = {}
_now = 1760000000

function time() return _now end
function GetBuildInfo() return "1.60.1", "70338", "Oct 1 2026", 16001 end
function UnitName() return "Tester" end
function UnitFactionGroup() return harness.faction end
function GetRealmName() return harness.realm end
function GetZoneText() return harness.zone end
function GetSubZoneText() return harness.subzone end
function GetCurrentRegionName() return "US" end
function GetCurrentRegion() return 1 end
function GetLocale() return "enUS" end

DEFAULT_CHAT_FRAME = { AddMessage = function(_, msg) table.insert(_chat, msg) end }
SlashCmdList = {}

function CreateFrame()
  local frame = { events = {} }
  function frame:RegisterEvent(e) self.events[e] = true end
  function frame:UnregisterEvent(e) self.events[e] = nil end
  function frame:SetScript(_, fn) self.onEvent = fn end
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

C_Item = {
  DoesItemExistByID = function(id) return id ~= 999999 end,
  RequestLoadItemDataByID = function(id)
    harness.requested[id] = true
    C_Timer.After(harness.metadataDelay or 0, function()
      if harness.metadataPending then harness.metadataPending[id] = nil end
      _fire("ITEM_KEY_ITEM_INFO_RECEIVED", id)
    end)
  end,
}

Enum = {
  CompressionMethod = { Deflate = 0 },
  AuctionHouseSortOrder = { Price = 1, Buyout = 2 },
  AuctionStatus = { Active = 0, Sold = 1 },
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
  for i = 1, #harness.auctions do
    local a = harness.auctions[i]
    if a.itemID == itemID and a.isCommodity == commodity then return a end
  end
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

local function emitResults(kind, key, itemID)
  local event = harness.eventKind or "UPDATED"
  local delay = harness.eventDelay or 0
  C_Timer.After(delay, function()
    if harness.emitStale then
      _fire(kind == "commodity" and "COMMODITY_SEARCH_RESULTS_UPDATED" or "ITEM_SEARCH_RESULTS_UPDATED", kind == "commodity" and (itemID + 999999) or makeKey(itemID + 999999, 0, 0, 0))
    end
    if event ~= "NONE" then
      local name = (kind == "commodity" and "COMMODITY_SEARCH_RESULTS_" or "ITEM_SEARCH_RESULTS_") .. event
      if kind == "commodity" then _fire(name, itemID) else _fire(name, makeKey(key.itemID, key.itemLevel, key.itemSuffix, key.battlePetSpeciesID)) end
    end
  end)
end

C_AuctionHouse = {
  IsThrottledMessageSystemReady = function()
    if harness.forceThrottle then return false end
    local count = 0
    for _, sent in ipairs(harness.sendLog or {}) do if _now - sent.at < 60 then count = count + 1 end end
    return count < 100
  end,
  MakeItemKey = function(itemID, itemLevel, itemSuffix, battlePetSpeciesID)
    return makeKey(itemID, itemLevel or 0, itemSuffix or 0, battlePetSpeciesID or 0)
  end,
  GetItemKeyInfo = function(key, restrictQualityToFilter)
    local itemID = keyValues(key)
    if not itemID or (harness.metadataPending and harness.metadataPending[itemID]) then return nil end
    local a = findAuction(itemID, true) or findAuction(itemID, false)
    return { itemID = itemID, battlePetSpeciesID = key.battlePetSpeciesID or 0, itemName = a and a.name or ("Item " .. itemID),
      quality = a and a.quality or 1, iconFileID = 1, isPet = (key.battlePetSpeciesID or 0) > 0,
      isCommodity = a and a.isCommodity == true or false, isEquipment = false }
  end,
  SendSellSearchQuery = function(key, sorts, separateOwnerItems)
    assert(type(key) == "table" and type(sorts) == "table" and type(separateOwnerItems) == "boolean", "documented SendSellSearchQuery signature")
    local itemID = keyValues(key)
    local commodity = findAuction(itemID, true) ~= nil
    harness.queryCalls = harness.queryCalls + 1
    harness.lastQuery = { key = key, itemID = itemID, commodity = commodity, loaded = 0 }
    local rows = queryRows(itemID, commodity)
    harness.lastQuery.loaded = math.min(harness.pageSize or 50, #rows)
    harness.lastQuery.full = not harness.forceIncomplete and harness.lastQuery.loaded >= #rows
    appendSend("search", itemID)
    _fire("AUCTION_HOUSE_THROTTLED_MESSAGE_SENT")
    _fire("AUCTION_HOUSE_THROTTLED_MESSAGE_RESPONSE_RECEIVED")
    emitResults(commodity and "commodity" or "item", key, itemID)
  end,
  SendSearchQuery = function(key, sorts, separateOwnerItems, minLevelFilter, maxLevelFilter)
    assert(type(key) == "table" and type(sorts) == "table" and type(separateOwnerItems) == "boolean", "documented SendSearchQuery signature")
    return C_AuctionHouse.SendSellSearchQuery(key, sorts, separateOwnerItems)
  end,
  RequestMoreCommoditySearchResults = function(itemID)
    assert(harness.lastQuery and harness.lastQuery.commodity and harness.lastQuery.itemID == itemID)
    local rows = queryRows(itemID, true)
    harness.lastQuery.loaded = math.min(harness.lastQuery.loaded + (harness.pageSize or 50), #rows)
    harness.lastQuery.full = not harness.forceIncomplete and harness.lastQuery.loaded >= #rows
    harness.queryCalls = harness.queryCalls + 1
    appendSend("commodity_page", itemID)
    _fire("AUCTION_HOUSE_THROTTLED_MESSAGE_SENT")
    _fire("AUCTION_HOUSE_THROTTLED_MESSAGE_RESPONSE_RECEIVED")
    emitResults("commodity", harness.lastQuery.key, itemID)
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
    _fire("AUCTION_HOUSE_THROTTLED_MESSAGE_SENT")
    _fire("AUCTION_HOUSE_THROTTLED_MESSAGE_RESPONSE_RECEIVED")
    emitResults("item", key, itemID)
    return harness.lastQuery.full
  end,
  HasFullCommoditySearchResults = function(itemID)
    return harness.lastQuery and harness.lastQuery.commodity and harness.lastQuery.itemID == itemID and harness.lastQuery.full or false
  end,
  HasFullItemSearchResults = function(key)
    local itemID = keyValues(key)
    return harness.lastQuery and not harness.lastQuery.commodity and harness.lastQuery.itemID == itemID and harness.lastQuery.full or false
  end,
  GetNumItemSearchResults = function(key)
    local itemID = keyValues(key); if not harness.lastQuery or harness.lastQuery.commodity or harness.lastQuery.itemID ~= itemID then return 0 end
    return math.min(harness.lastQuery.loaded, #queryRows(itemID, false))
  end,
  GetItemSearchResultInfo = function(key, index)
    local itemID = keyValues(key); local rows = queryRows(itemID, false)
    if not harness.lastQuery or harness.lastQuery.commodity or harness.lastQuery.itemID ~= itemID or index > harness.lastQuery.loaded or
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

    def __post_init__(self) -> None:
        self.lua = lua51.LuaRuntime(unpack_returned_tuples=True, encoding="latin-1")
        self.state = self.lua.table_from(
            {
                "faction": self.faction,
                "realm": self.realm,
                "zone": self.zone,
                "subzone": self.subzone,
                "requested": self.lua.table(),
                "queryCalls": 0,
                "ownedQueries": 0,
                "auctions": self.lua.table(),
                "owned": self.lua.table(),
                "ownedFull": True,
                "emitOwnedEvent": True,
                "sendLog": self.lua.table(),
                "missingResults": self.lua.table(),
            }
        )
        self.lua.execute("return function(...) " + STUBS + " end")(self.state)
        self._install_codec()
        self.ns = self.lua.table()
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
                    return {}
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

    def set_owned(self, auctions: list[Auction], *, complete: bool = True) -> None:
        table = self.lua.table()
        for i, auction in enumerate(auctions, start=1):
            table[i] = self._to_lua(auction.__dict__)
        self.state.owned = table
        self.state.ownedFull = complete

    def set_metadata_pending(self, item_ids: list[int]) -> None:
        self.state.metadataPending = self._to_lua({item_id: True for item_id in item_ids})

    def set_event_behavior(self, *, kind: str = "UPDATED", delay: int = 0, stale: bool = False) -> None:
        self.state.eventKind = kind
        self.state.eventDelay = delay
        self.state.emitStale = stale

    def external_search(self, item_id: int) -> None:
        key = self.lua.globals().C_AuctionHouse.MakeItemKey(item_id, 0, 0, 0)
        sorts = self.lua.table()
        sorts[1] = self._to_lua({"sortOrder": 1, "reverseSort": False})
        self.lua.globals().C_AuctionHouse.SendSearchQuery(key, sorts, False, 0, 0)

    def set_owned_behavior(self, *, complete: bool = True, emit: bool = True, delay: int = 0) -> None:
        self.state.ownedFull = complete
        self.state.emitOwnedEvent = emit
        self.state.ownedDelay = delay

    def set_throttled(self, throttled: bool = True) -> None:
        self.state.forceThrottle = throttled

    @property
    def send_log(self) -> list[dict]:
        return [dict(entry.items()) for entry in self.state.sendLog.values()]

    def set_plan(self, item_ids: list[int]) -> None:
        body = {
            "schemaVersion": 2,
            "id": "first-run",
            "revision": 1,
            "catalogHash": "a" * 64,
            "targetClientBuild": "1.60.1.1",
            "cadenceSeconds": 900,
            "initialPriceLevels": 20,
            "itemIDs": sorted(item_ids),
            "pools": {"core": sorted(item_ids), "discovery": []},
        }
        plan_json = json.dumps(body, sort_keys=True, separators=(",", ":"))
        plan = {**body, "planHash": hashlib.sha256(plan_json.encode()).hexdigest(), "planJSON": plan_json}
        self.lua.globals().CROWLEY_DATA.scanPlan = self._to_lua(plan)

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

    def run_timers(self) -> None:
        self.lua.globals()._runTimers()

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
