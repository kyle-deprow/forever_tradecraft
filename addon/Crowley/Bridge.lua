local _, ns = ...

-- Pushes shopping lists computed by the server (via Crowley_Data) into Auctionator.
local Bridge = {}
ns.Bridge = Bridge

local CALLER = "Crowley"

-- CROWLEY_DATA.shoppingLists = { { name = "...", house = "us-normal-horde",
--   items = { { name = "Linen Cloth", maxPrice = 1200, quantity = 200 } } } }
function Bridge.SyncShoppingLists(houseKey)
  local v1 = Auctionator.API.v1
  local created = 0
  for _, list in ipairs(CROWLEY_DATA.shoppingLists) do
    if list.house == houseKey then
      local searchStrings = {}
      for _, item in ipairs(list.items) do
        searchStrings[#searchStrings + 1] = v1.ConvertToSearchString(CALLER, {
          searchString = item.name,
          isExact = true,
          maxPrice = item.maxPrice,
          quantity = item.quantity,
        })
      end
      v1.CreateShoppingList(CALLER, list.name, searchStrings)
      created = created + 1
    end
  end
  return created
end

-- Sync once per data generation and house, when the AH opens.
ns.On("AUCTION_HOUSE_SHOW", function()
  local houseKey = ns.Context.House().key
  local marker = CROWLEY_DATA.generatedAt .. ":" .. houseKey
  if ns.db.lastListSync == marker then return end
  ns.db.lastListSync = marker
  local created = Bridge.SyncShoppingLists(houseKey)
  if created > 0 then
    ns.Print(("synced %d shopping list(s) to Auctionator for %s"):format(created, houseKey))
  end
end)
