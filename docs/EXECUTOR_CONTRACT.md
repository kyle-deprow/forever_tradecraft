# Trade executor contract (queue → addon → results)

Parent-authored contract shared by the server/companion queue pipeline and the addon executor. Neither side
changes it alone. Money is integer copper; items are numeric item IDs (never names).

## Safety model
- Nothing trades unless **both** arms are set: the published queue has `armed = true`, **and** someone typed
  `/crowley arm <queueId>` in the current game session (session-local; cleared by any reload or logout). Otherwise
  every click is a **dry run**: the executor resolves and validates the action, shows "dry run: would …", records a
  `dry_run` result and makes no protected call.
- One protected API call per hardware click on the executor button. The button never chains protected calls.
- Automated clicking (when it exists) is capped at one click per second by the session driver (CLAUDE.md); the addon
  additionally refuses a click that arrives less than 1.0 s after the previous executor click (`too_fast`).
- Any mismatch fails closed: the action is refused with a reason code and the executor stops at it until skipped or
  the queue is replaced.

## Queue file
The companion writes `Interface/AddOns/Crowley_Data/Queue.lua`, loaded by `Crowley_Data.toc` after `Data.lua`,
assigning one global (never a key inside `CROWLEY_DATA`, whose keys the session daemon reads strictly):

```lua
CROWLEY_QUEUE = {
  format = 1,
  queueId = "<house>-<character>-<generatedAt>-<4 hex>",  -- unique
  generatedAt = <epoch seconds>,
  expiresAt = <epoch seconds>,          -- executor refuses after this time (`expired`)
  house = "<house key>",                 -- must equal ns.Context.House().key (`house_mismatch`)
  character = "<name>",                  -- must equal UnitName("player") (`character_mismatch`)
  armed = false,                         -- server-side arm (see safety model)
  actions = {                            -- array, executed in order
    { seq = 1, kind = "buy_commodity",  itemID = 2589, quantity = 20, maxUnitPrice = 25 },
    { seq = 2, kind = "post_commodity", itemID = 2589, quantity = 20, unitPrice = 30, durationHours = 12 },
    { seq = 3, kind = "cancel_auction", auctionID = 123456789 },
    { seq = 4, kind = "vendor_sell",    itemID = 2589, quantity = 20 },
    { seq = 5, kind = "vendor_buy",     itemID = 3371, quantity = 5 },     -- whole vendor bundles
    { seq = 6, kind = "craft",          recipeID = 2963, times = 1 },      -- recipeID = spell ID
    { seq = 7, kind = "mail_collect",   maxMessages = 10 },
  },
}
```
`Queue.lua` with no queue assigns `CROWLEY_QUEUE = false`. Field rules: `seq` 1..n contiguous; positive integers
everywhere; `durationHours` ∈ {12, 24, 48}; at most 50 actions; `expiresAt > generatedAt`.

## Execution per kind (one hardware click each unless stated)
| kind | requires open | click behaviour |
|---|---|---|
| buy_commodity | AH | click 1: `C_AuctionHouse.StartCommoditiesPurchase(itemID, quantity)`; on `COMMODITY_PRICE_UPDATED(unitPrice, totalPrice)` refuse (`price_above_max`, then `CancelCommoditiesPurchase`) if `unitPrice > maxUnitPrice`; click 2: `ConfirmCommoditiesPurchase(itemID, quantity)`; success on `COMMODITY_PURCHASE_SUCCEEDED`, failure on `COMMODITY_PURCHASE_FAILED` |
| post_commodity | AH | find a bag stack of `itemID` with ≥ quantity (`C_Container`), `ItemLocation:CreateFromBagAndSlot`, check `C_AuctionHouse.IsSellItemValid`, record `CalculateCommodityDeposit`; click: `C_AuctionHouse.PostCommodity(location, duration, quantity, unitPrice)` with duration 1/2/3 for 12/24/48 h; success on `AUCTION_HOUSE_AUCTION_CREATED` |
| cancel_auction | AH | `C_AuctionHouse.CanCancelAuction(auctionID)` must be true; record `GetCancelCost`; click: `CancelAuction(auctionID)`; success on `AUCTION_CANCELED` |
| vendor_sell | merchant | find bag slots holding `itemID` totalling ≥ quantity, exact stacks only (no splitting; refuse `stack_mismatch` otherwise); one click per stack: `C_Container.UseContainerItem(bag, slot)` |
| vendor_buy | merchant | find merchant index with `GetMerchantItemID(i) == itemID`; click: `BuyMerchantItem(index, quantity)` |
| craft | profession window (`C_TradeSkillUI.IsTradeSkillReady()`) | recipe learned (`C_TradeSkillUI.GetRecipeInfo(recipeID).learned`) and `GetCraftableCount(recipeID) >= times`; click: `C_TradeSkillUI.CraftRecipe(recipeID, times)` |
| mail_collect | mailbox | one click per message: `AutoLootMailItem(index)` (money and items), up to `maxMessages` |

Assumption: these calls behave as their names suggest in the Forever client (presence verified by probe 1792639338;
behaviour is not). Every assumption is confirmed live in dry run first, then one armed action at a time.

## Results
The addon appends to `CrowleyDB.executions[queueId] = { queueId, house, character, results = { ... } }`, one result per
attempted action: `{ seq, kind, status, at, detail }` with `status` ∈ {`dry_run`, `started`, `succeeded`, `failed`,
`refused`, `skipped`} and `detail` holding observed values (unitPrice/totalPrice for buys, deposit for posts, cancel cost,
bag/slot used, merchant index, error event text). The companion uploads each queue's execution record once it changes;
the server stores it and reconciles it against the queue.
