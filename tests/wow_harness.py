"""Runs the real addon Lua under Lua 5.1 (WoW's version) against a fake WoW client API."""

from __future__ import annotations

import base64
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from lupa import lua51

ADDONS = Path(__file__).resolve().parents[1] / "addon"

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

C_Timer = { After = function(delay, fn) table.insert(_timers, fn) end }

function _runTimers()
  local guard = 0
  while #_timers > 0 do
    local fn = table.remove(_timers, 1)
    fn()
    guard = guard + 1
    if guard > 100000 then error("timer loop") end
  end
end

C_Item = {
  DoesItemExistByID = function(id) return id ~= 999999 end,
  RequestLoadItemDataByID = function(id) harness.requested[id] = true end,
}

Enum = { CompressionMethod = { Deflate = 0 } }

-- Records what the addon pushes into Auctionator.
_lists = {}
Auctionator = { API = { v1 = {
  ConvertToSearchString = function(caller, term)
    return ('"%s";;;;;;;;;%s;;;;%s'):format(term.searchString, term.maxPrice / 10000, term.quantity)
  end,
  CreateShoppingList = function(caller, name, items) _lists[name] = items end,
} } }

C_AuctionHouse = {
  ReplicateItems = function() harness.replicateCalls = harness.replicateCalls + 1 end,
  GetNumReplicateItems = function() return #harness.auctions end,
  GetReplicateItemInfo = function(i)
    local a = harness.auctions[i + 1]
    local hasAll = a.hasAllInfo
    if hasAll == false and harness.requested[a.itemID] then hasAll = true end
    return a.name, 0, a.count, a.quality, true, a.level, "", a.minBid, 0, a.buyout, a.bid,
      false, nil, a.owner, a.owner, 0, a.itemID, hasAll
  end,
  GetReplicateItemLink = function(i) return harness.auctions[i + 1].link end,
  GetReplicateItemTimeLeft = function(i) return harness.auctions[i + 1].timeLeft end,
}

-- Mimics how the client serialises SavedVariables: bracketed keys, %q strings.
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

    def __post_init__(self) -> None:
        if not self.link:
            self.link = f"|Hitem:{self.itemID}::::::::60:::::::::|h[{self.name}]|h"


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
                "replicateCalls": 0,
                "auctions": self.lua.table(),
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

        g = self.lua.globals()
        g.C_EncodingUtil = self.lua.table_from(
            {
                "CompressString": compress,
                "EncodeBase64": lambda b: base64.b64encode(raw(b)).decode(),
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
        for i, a in enumerate(auctions, start=1):
            table[i] = self.lua.table_from(a.__dict__)
        self.state.auctions = table

    def fire(self, event: str, *args) -> None:
        self.lua.globals()._fire(event, *args)

    def run_timers(self) -> None:
        self.lua.globals()._runTimers()

    def advance(self, seconds: int) -> None:
        g = self.lua.globals()
        g._now = g._now + seconds

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
