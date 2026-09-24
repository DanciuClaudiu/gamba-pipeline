# Pipeline report

Built 2026-09-24 with `uv run gamba-pipeline` from the inputs pinned in `inputs.toml`.
Complete lists of rejected and flagged rows: `build/report/*.csv` (local, not committed).

## Inputs

| Input | Release | SHA-256 |
|---|---|---|
| foundation | 2026-04-30 | `70457ee9d9342f43…` |
| sr_legacy | 2018-04 | `b80817294b885053…` |
| exercises | a859101d633a01c4a1a920d6a8ce41dabba0705f | `5bb747e3fc658f09…` |
| off | 3dc10b5483b8401e25390ef71b0391726137643d | `138d64179619ea7d…` |
| branded | 2026-04-30 | `26050a5d03197469…` |

## Reference database

|  |  |
|---|---|
| Foods | 8,032 (Foundation 329, SR Legacy 7,703) |
| Rejected | 91 |
| Duplicate names (kept Foundation) | 139 |
| Flagged | 142 |
| Carbs set to 0 g | 10 |
| Exercises | 739 (weightReps 605, bodyweightReps 123, duration 10, assisted 1) |
| Size | 2.5 MB |
| SHA-256 | `530bf8f608e36728f9dba1439d24d8f5046ce0e8df2d5ec98ad6779a3cdf6bf7` |

## Packs

| Pack | Products | Complete | Size | Download | Rejected | Flagged | Named by brand | Left out (no name or brand) |
|---|---|---|---|---|---|---|---|---|
| food-gb | 149,156 | 147,488 | 35.1 MB | 13.4 MB | 359 | 5,178 | 535 | 1,270 |
| food-ro | 13,047 | 12,733 | 3.2 MB | 1.3 MB | 55 | 355 | 87 | 272 |
| food-us | 849,773 | 832,652 | 215.6 MB | 77.0 MB | 21,520 | 39,416 | 259 | 798 |

### What was read

Products read from Open Food Facts (and USDA Branded for the US), and those left out before validation.

| Pack | Read | Without energy | Invalid barcode | Duplicate barcode |
|---|---|---|---|---|
| food-gb | 194,241 | 42,128 | 1,327 | 1 |
| food-ro | 46,831 | 33,392 | 65 | 0 |
| food-us | 1,437,576 | 144,169 | 66,732 | 22,885 |

### Why rows were rejected

| Reason | food-gb | food-ro | food-us |
|---|---|---|---|
| a negative value | 3 | 0 | 4 |
| energy over the limit | 236 | 21 | 920 |
| protein + carbs + fat over 105 g | 120 | 34 | 20,596 |

### USDA Branded merge

| Pack | In both | USDA nutrients kept | USDA only |
|---|---|---|---|
| food-us | 331,699 | 20,196 | 89,486 |

### Flagged rows

Energy that doesn't match 4P + 4C + 9F by more than max(20 kcal, 20%). Kept and never fixed (P12). The first 5 per pack:

| Pack | GTIN-14 | Name | Why |
|---|---|---|---|
| food-gb | `00000000002523` | Peach | energy 38 kcal, macros give 75 kcal |
| food-gb | `00000000012126` | Passion fruit | energy 58 kcal, macros give 38 kcal |
| food-gb | `00000000019071` | Scottish Free Range Large Egg | energy 131 kcal, macros give 83 kcal |
| food-gb | `00000000022750` | MOZZARELLA STICKS | energy 616 kcal, macros give 305 kcal |
| food-gb | `00000000048644` | Mexican Taco Kit | energy 106 kcal, macros give 693 kcal |
| food-ro | `00000007526008` | Bere neagră premium | energy 58 kcal, macros give 20 kcal |
| food-ro | `00000015783066` | Castraveți murați | energy 55 kcal, macros give 11 kcal |
| food-ro | `00000020094508` | Crefee mit feinen Kräutern | energy 163 kcal, macros give 243 kcal |
| food-ro | `00000020127206` | mici de porc | energy 10 kcal, macros give 263 kcal |
| food-ro | `00000020128883` | BUTTER CHICKEN | energy 54 kcal, macros give 161 kcal |
| food-us | `00000000001250` | Bismarckheringe 3,00 kg Kübel | energy 176 kcal, macros give 356 kcal |
| food-us | `00000000007122` | Test | energy 373 kcal, macros give 0 kcal |
| food-us | `00000000008686` | Roasted & salted peanuts | energy 1 kcal, macros give 533 kcal |
| food-us | `00000000009973` | Leonardo | energy 609 kcal, macros give 296 kcal |
| food-us | `00000000010672` | Dominican Dark Chocolate | energy 484 kcal, macros give 592 kcal |

## Spot checks

The most-scanned products in each country (`spotchecks/<country>.json`), looked up by barcode and by name, with the per-100 values of their source record.

| Pack | Products | By barcode | By name | Values | Passed |
|---|---|---|---|---|---|
| food-gb | 20 | 20 | 20 | 20 | 20 |
| food-ro | 20 | 20 | 20 | 20 | 20 |
| food-us | 20 | 20 | 20 | 20 | 20 |

## Pack threshold (Q5)

Products per country with energy, a valid barcode and a name or brand, before validation. Sizes are estimated at 251 bytes per product, the average of the packs built above. Downloads are about 36% of the size.

| At least | Countries | Products | Estimated size |
|---|---|---|---|
| 1,000 | 83 | 3,481,113 | 873.4 MB |
| 2,000 | 62 | 3,451,294 | 865.9 MB |
| 5,000 | 44 | 3,390,577 | 850.7 MB |
| 10,000 | 27 | 3,271,216 | 820.8 MB |
| 20,000 | 16 | 3,103,541 | 778.7 MB |

**Proposal:** keep 5,000 products, the SPEC's starting point: 44 packs, well inside Apple's 200 asset packs per app. Countries:

| Country | Products | Estimated size |
|---|---|---|
| France | 884,904 | 222.0 MB |
| United States | 778,605 | 195.4 MB |
| Spain | 248,757 | 62.4 MB |
| Germany | 239,167 | 60.0 MB |
| Italy | 217,458 | 54.6 MB |
| United Kingdom | 149,509 | 37.5 MB |
| Canada | 108,731 | 27.3 MB |
| Switzerland | 87,051 | 21.8 MB |
| Belgium | 80,729 | 20.3 MB |
| Australia | 66,440 | 16.7 MB |
| Ireland | 65,681 | 16.5 MB |
| Netherlands | 58,612 | 14.7 MB |
| Japan | 40,943 | 10.3 MB |
| Brazil | 27,638 | 6.9 MB |
| Sweden | 24,680 | 6.2 MB |
| Poland | 24,636 | 6.2 MB |
| Finland | 19,283 | 4.8 MB |
| Austria | 19,077 | 4.8 MB |
| Norway | 18,932 | 4.8 MB |
| Denmark | 18,685 | 4.7 MB |
| Portugal | 15,275 | 3.8 MB |
| Czech Republic | 15,236 | 3.8 MB |
| Romania | 13,097 | 3.3 MB |
| New Zealand | 12,937 | 3.2 MB |
| Mexico | 12,588 | 3.2 MB |
| Russia | 11,628 | 2.9 MB |
| Bulgaria | 10,937 | 2.7 MB |
| Luxembourg | 9,813 | 2.5 MB |
| Morocco | 9,632 | 2.4 MB |
| Hungary | 9,107 | 2.3 MB |
| India | 8,722 | 2.2 MB |
| Thailand | 8,145 | 2.0 MB |
| Greece | 8,086 | 2.0 MB |
| Israel | 7,115 | 1.8 MB |
| Lithuania | 6,883 | 1.7 MB |
| Argentina | 6,736 | 1.7 MB |
| South Africa | 6,082 | 1.5 MB |
| Singapore | 6,026 | 1.5 MB |
| Croatia | 5,760 | 1.4 MB |
| Estonia | 5,687 | 1.4 MB |
| Turkey | 5,644 | 1.4 MB |
| Slovakia | 5,424 | 1.4 MB |
| Saudi Arabia | 5,387 | 1.4 MB |
| Ukraine | 5,112 | 1.3 MB |
