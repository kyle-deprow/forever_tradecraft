# Provisional beta portfolio evidence

Comparable replay: house `beta-normal-alliance`, build `1.60.1.70450`, 290 selected sweeps, 20g start, equal capital across the two crafting strategies plus dip_reversion/vendor_arb, demand_share 0.5, 24h wind-down, empty explicit tool/category/focus capabilities. All ten pairs use the same data and source digest.

| Professions | Realized profit (g) | Modeled clicks |
|---|---:|---:|
| alchemy + engineering | 60.7899 | 3512 |
| alchemy + leatherworking | 49.2384 | 4173 |
| alchemy + blacksmithing | 48.1085 | 3208 |
| blacksmithing + engineering | 38.7944 | 2494 |
| alchemy + tailoring | 34.0434 | 2776 |
| engineering + leatherworking | 30.7753 | 3399 |
| engineering + tailoring | 23.4400 | 2089 |
| blacksmithing + leatherworking | 22.5818 | 3226 |
| blacksmithing + tailoring | 8.3636 | 1812 |
| leatherworking + tailoring | 7.3544 | 2768 |

Provisional new-paper portfolio: crafting_alchemy, crafting_engineering, dip_reversion, vendor_arb, in that exact measured order and equal weights. Explicit historical/research portfolios remain available. No live run was created or changed.

The leading pair has 60.7899g realized profit and 718.3512g final modeled equity, including 637.5613g unrealized marks. Maximum drawdown 52.88%; 393 posts, 161 expired listings (not a unit expiry percentage), 6.5528g lost deposits. 3512 modeled clicks imply a 58.53-minute minimum at 1 click/s; this excludes crafting time, walking, UI waits, focus recovery and real timing. It is not a measured time on the live AH.

Larger marked holdings and gappy beta history limit the evidence. Recipe learnability, live tools/stations, actual sales, demand estimator accuracy, launch prices and native protected APIs remain unqualified. Bronze Tube stays blocked under the empty capabilities. This is not a pure before/after station delta: the historical doc used 236 sweeps, while this comparison uses 290.

Listing/expiry controls passed independent Sol review; four same-data policy variants completed and the baseline exactly reproduced. Shortening auctions, smaller exposure, and optional repricing all returned less realized profit with more clicks than the 24h baseline; retain listing defaults/repricing off. See docs/TRADING.md and listing-policy-comparison.json for complete aggregates. Detailed raw reports and source books remain under private local state; aggregate JSON records the source digest and private report location.
