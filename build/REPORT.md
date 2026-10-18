# Pipeline report

Built 2026-10-18 with `uv run gamba-pipeline` from the inputs pinned in `inputs.toml`.
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
| SHA-256 | `955de26c78fcba941cb0d87e98c3e7ca0151c8fe96723fd18e8687977c56b36b` |

## Packs

| Pack | Products | Complete | Size | Download | Rejected | Flagged | Named by brand | Left out (no name or brand) |
|---|---|---|---|---|---|---|---|---|
| food-ar | 6,700 | 6,241 | 1.6 MB | 0.6 MB | 39 | 190 | 22 | 44 |
| food-at | 19,055 | 18,547 | 4.5 MB | 1.8 MB | 25 | 383 | 48 | 105 |
| food-au | 66,276 | 65,342 | 15.9 MB | 6.2 MB | 164 | 3,839 | 32 | 104 |
| food-be | 80,614 | 79,931 | 17.8 MB | 6.8 MB | 123 | 3,867 | 201 | 336 |
| food-bg | 10,908 | 10,620 | 2.8 MB | 1.1 MB | 35 | 291 | 64 | 208 |
| food-br | 27,434 | 24,831 | 6.6 MB | 2.5 MB | 207 | 2,778 | 86 | 80 |
| food-ca | 108,540 | 107,935 | 25.4 MB | 9.6 MB | 192 | 4,736 | 40 | 117 |
| food-ch | 86,917 | 85,805 | 20.4 MB | 8.2 MB | 136 | 3,607 | 199 | 203 |
| food-cz | 15,211 | 14,848 | 3.6 MB | 1.5 MB | 28 | 232 | 37 | 76 |
| food-de | 238,805 | 233,302 | 54.7 MB | 21.1 MB | 371 | 6,880 | 774 | 841 |
| food-dk | 18,658 | 18,195 | 4.2 MB | 1.6 MB | 29 | 208 | 40 | 89 |
| food-ee | 5,684 | 5,667 | 1.3 MB | 0.5 MB | 3 | 48 | 2 | 16 |
| food-es | 248,114 | 245,768 | 52.5 MB | 18.3 MB | 661 | 16,700 | 583 | 1,360 |
| food-fi | 19,276 | 18,817 | 4.4 MB | 1.7 MB | 9 | 261 | 24 | 49 |
| food-fr | 883,730 | 874,968 | 193.8 MB | 69.5 MB | 1,219 | 39,897 | 1,658 | 2,942 |
| food-gb | 149,156 | 147,488 | 35.1 MB | 13.4 MB | 359 | 5,178 | 535 | 1,270 |
| food-gr | 8,059 | 7,826 | 2.0 MB | 0.8 MB | 33 | 198 | 25 | 173 |
| food-hr | 5,752 | 5,658 | 1.4 MB | 0.6 MB | 9 | 83 | 27 | 38 |
| food-hu | 9,081 | 8,860 | 2.1 MB | 0.9 MB | 27 | 181 | 50 | 95 |
| food-ie | 65,468 | 56,776 | 14.6 MB | 6.0 MB | 214 | 1,808 | 107 | 139 |
| food-il | 7,105 | 6,856 | 1.8 MB | 0.7 MB | 10 | 93 | 3 | 15 |
| food-in | 8,675 | 8,416 | 2.0 MB | 0.8 MB | 51 | 215 | 29 | 144 |
| food-it | 217,066 | 215,228 | 45.7 MB | 16.0 MB | 400 | 10,997 | 226 | 505 |
| food-jp | 40,881 | 39,043 | 10.1 MB | 4.2 MB | 62 | 548 | 19 | 21 |
| food-lt | 6,873 | 6,813 | 1.7 MB | 0.7 MB | 10 | 54 | 17 | 30 |
| food-lu | 9,801 | 9,366 | 2.2 MB | 0.9 MB | 12 | 313 | 9 | 21 |
| food-ma | 9,579 | 9,315 | 2.1 MB | 0.9 MB | 65 | 732 | 49 | 275 |
| food-mx | 12,498 | 12,039 | 3.0 MB | 1.2 MB | 91 | 418 | 90 | 68 |
| food-nl | 58,531 | 57,229 | 13.7 MB | 5.3 MB | 82 | 1,070 | 140 | 355 |
| food-no | 18,904 | 18,451 | 4.5 MB | 1.8 MB | 29 | 347 | 16 | 41 |
| food-nz | 12,882 | 12,572 | 3.2 MB | 1.2 MB | 56 | 514 | 10 | 38 |
| food-pl | 24,600 | 24,020 | 5.9 MB | 2.3 MB | 40 | 397 | 130 | 217 |
| food-pt | 15,229 | 14,998 | 3.7 MB | 1.4 MB | 50 | 375 | 108 | 245 |
| food-ro | 13,047 | 12,733 | 3.2 MB | 1.3 MB | 55 | 355 | 87 | 272 |
| food-ru | 11,605 | 10,278 | 3.1 MB | 1.2 MB | 29 | 222 | 41 | 231 |
| food-sa | 5,354 | 5,138 | 1.3 MB | 0.5 MB | 33 | 226 | 4 | 16 |
| food-se | 24,650 | 24,180 | 5.5 MB | 2.1 MB | 30 | 349 | 64 | 133 |
| food-sg | 6,003 | 5,914 | 1.5 MB | 0.6 MB | 23 | 136 | 4 | 15 |
| food-sk | 5,413 | 5,104 | 1.3 MB | 0.6 MB | 11 | 149 | 12 | 50 |
| food-th | 8,077 | 7,742 | 2.6 MB | 1.0 MB | 68 | 185 | 6 | 20 |
| food-tr | 5,623 | 5,432 | 1.4 MB | 0.6 MB | 21 | 159 | 14 | 88 |
| food-ua | 5,104 | 4,961 | 1.4 MB | 0.6 MB | 10 | 72 | 13 | 75 |
| food-us | 849,773 | 832,652 | 215.6 MB | 77.0 MB | 21,520 | 39,416 | 259 | 798 |
| food-za | 6,030 | 5,711 | 1.5 MB | 0.6 MB | 54 | 244 | 6 | 31 |
| Total | 3,456,741 | 3,391,616 | 802.7 MB | 296.2 MB | 26,695 | 148,951 | 5,910 | 11,989 |

### What was read

Products read from Open Food Facts (and USDA Branded for the US), and those left out before validation.

| Pack | Read | Without energy | Invalid barcode | Duplicate barcode |
|---|---|---|---|---|
| food-ar | 16,204 | 9,369 | 52 | 0 |
| food-at | 22,802 | 3,466 | 151 | 0 |
| food-au | 81,377 | 14,394 | 439 | 0 |
| food-be | 101,420 | 19,497 | 850 | 0 |
| food-bg | 17,950 | 6,721 | 78 | 0 |
| food-br | 35,969 | 8,067 | 181 | 0 |
| food-ca | 126,019 | 15,574 | 1,574 | 22 |
| food-ch | 105,343 | 17,089 | 997 | 1 |
| food-cz | 20,782 | 5,399 | 68 | 0 |
| food-de | 426,081 | 184,514 | 1,550 | 0 |
| food-dk | 22,302 | 2,528 | 998 | 0 |
| food-ee | 6,502 | 781 | 18 | 0 |
| food-es | 358,505 | 93,014 | 15,343 | 13 |
| food-fi | 20,818 | 1,416 | 67 | 1 |
| food-fr | 1,262,790 | 361,199 | 13,654 | 46 |
| food-gb | 194,241 | 42,128 | 1,327 | 1 |
| food-gr | 12,576 | 4,240 | 71 | 0 |
| food-hr | 7,634 | 1,812 | 23 | 0 |
| food-hu | 11,580 | 2,328 | 49 | 0 |
| food-ie | 79,557 | 8,888 | 4,844 | 4 |
| food-il | 8,422 | 1,245 | 47 | 0 |
| food-in | 23,087 | 14,111 | 106 | 0 |
| food-it | 270,144 | 50,097 | 2,072 | 4 |
| food-jp | 44,832 | 3,566 | 302 | 0 |
| food-lt | 11,036 | 4,087 | 36 | 0 |
| food-lu | 11,276 | 1,396 | 46 | 0 |
| food-ma | 22,256 | 12,314 | 23 | 0 |
| food-mx | 17,660 | 4,591 | 412 | 0 |
| food-nl | 109,929 | 50,279 | 682 | 0 |
| food-no | 27,075 | 7,962 | 138 | 1 |
| food-nz | 15,701 | 2,656 | 69 | 0 |
| food-pl | 37,488 | 12,535 | 95 | 1 |
| food-pt | 22,465 | 6,880 | 61 | 0 |
| food-ro | 46,831 | 33,392 | 65 | 0 |
| food-ru | 36,409 | 19,906 | 4,637 | 1 |
| food-sa | 16,647 | 11,197 | 47 | 0 |
| food-se | 27,358 | 2,453 | 92 | 0 |
| food-sg | 11,539 | 5,404 | 94 | 0 |
| food-sk | 8,711 | 3,213 | 24 | 0 |
| food-th | 11,097 | 2,703 | 229 | 0 |
| food-tr | 11,401 | 5,646 | 23 | 0 |
| food-ua | 7,321 | 2,107 | 25 | 0 |
| food-us | 1,437,576 | 144,169 | 66,732 | 22,885 |
| food-za | 10,260 | 4,126 | 19 | 0 |

### Why rows were rejected

| Pack | a negative value | energy over the limit | protein + carbs + fat over 105 g |
|---|---|---|---|
| food-ar | 0 | 9 | 30 |
| food-at | 3 | 9 | 13 |
| food-au | 0 | 101 | 63 |
| food-be | 3 | 89 | 31 |
| food-bg | 1 | 13 | 21 |
| food-br | 0 | 40 | 167 |
| food-ca | 0 | 58 | 134 |
| food-ch | 7 | 95 | 34 |
| food-cz | 2 | 16 | 10 |
| food-de | 57 | 192 | 122 |
| food-dk | 2 | 14 | 13 |
| food-ee | 0 | 1 | 2 |
| food-es | 4 | 556 | 101 |
| food-fi | 0 | 5 | 4 |
| food-fr | 19 | 922 | 278 |
| food-gb | 3 | 236 | 120 |
| food-gr | 0 | 13 | 20 |
| food-hr | 0 | 4 | 5 |
| food-hu | 0 | 12 | 15 |
| food-ie | 1 | 81 | 132 |
| food-il | 0 | 3 | 7 |
| food-in | 0 | 7 | 44 |
| food-it | 7 | 289 | 104 |
| food-jp | 0 | 15 | 47 |
| food-lt | 0 | 4 | 6 |
| food-lu | 0 | 3 | 9 |
| food-ma | 0 | 27 | 38 |
| food-mx | 3 | 41 | 47 |
| food-nl | 3 | 55 | 24 |
| food-no | 1 | 13 | 15 |
| food-nz | 0 | 27 | 29 |
| food-pl | 3 | 13 | 24 |
| food-pt | 3 | 25 | 22 |
| food-ro | 0 | 21 | 34 |
| food-ru | 1 | 16 | 12 |
| food-sa | 0 | 10 | 23 |
| food-se | 3 | 15 | 12 |
| food-sg | 0 | 6 | 17 |
| food-sk | 1 | 9 | 1 |
| food-th | 0 | 15 | 53 |
| food-tr | 0 | 15 | 6 |
| food-ua | 0 | 4 | 6 |
| food-us | 4 | 920 | 20,596 |
| food-za | 0 | 38 | 16 |

### USDA Branded merge

| Pack | In both | USDA nutrients kept | USDA only |
|---|---|---|---|
| food-us | 331,699 | 20,196 | 89,486 |

### Flagged rows

Energy that doesn't match 4P + 4C + 9F by more than max(20 kcal, 20%). Kept and never fixed (P12). The first 2 per pack:

| Pack | GTIN-14 | Name | Why |
|---|---|---|---|
| food-ar | `00000075032715` | cerveza | energy 42 kcal, macros give 17 kcal |
| food-ar | `00000077900845` | Tita | energy 87 kcal, macros give 264 kcal |
| food-at | `00000003340042` | Simple Side Salad with Chive Dressing | energy 102 kcal, macros give 81 kcal |
| food-at | `00000009000018` | Protein Boost Trail Mix | energy 540 kcal, macros give 289 kcal |
| food-au | `00000002109282` | Taco Zesty Spice Mix | energy 105 kcal, macros give 135 kcal |
| food-au | `00000005529285` | Hot pepper sauce | energy 0 kcal, macros give 57 kcal |
| food-be | `00000000544290` | Mentos pure fresh chewing gum | energy 179 kcal, macros give 290 kcal |
| food-be | `00000000888615` | Chocolat chaud | energy 321 kcal, macros give 391 kcal |
| food-bg | `00000004734659` | Царевичен чипс | energy 403 kcal, macros give 127 kcal |
| food-bg | `00000018002263` | Краве прясно мляко | energy 235 kcal, macros give 57 kcal |
| food-br | `00000001238990` | Positive Vibration | energy 230 kcal, macros give 158 kcal |
| food-br | `00000009662292` | CHOCOLATE CHIP COOKIE DOUGH | energy 317 kcal, macros give 392 kcal |
| food-ca | `00000000001090` | Organic Corn | energy 120 kcal, macros give 20 kcal |
| food-ca | `00000000015998` | Blueberry Bleuets | energy 38 kcal, macros give 74 kcal |
| food-ch | `00000000051071` | Confit de piment doux bio | energy 254 kcal, macros give 316 kcal |
| food-ch | `00000000510295` | Gummibärchen | energy 201 kcal, macros give 318 kcal |
| food-cz | `00000000616195` | Mild Chili Powder | energy 349 kcal, macros give 277 kcal |
| food-cz | `00000008392473` | Dutch Cocoa powder | energy 288 kcal, macros give 222 kcal |
| food-de | `00000000000406` | Francais | energy 25 kcal, macros give 405 kcal |
| food-de | `00000000001250` | Bismarckheringe 3,00 kg Kübel | energy 176 kcal, macros give 356 kcal |
| food-dk | `00000012817542` | Mini Fourrés Fraise | energy 116 kcal, macros give 379 kcal |
| food-dk | `00000019414485` | Semințe pestrițe | energy 399 kcal, macros give 303 kcal |
| food-ee | `00000020171841` | Roggen Vollkorn-Knäckebr | energy 373 kcal, macros give 287 kcal |
| food-ee | `00715235567418` | Tiqle sticks boisson goût fraise | energy 29 kcal, macros give 0 kcal |
| food-es | `00000000000413` | Jamon gran reserva | energy 319 kcal, macros give 225 kcal |
| food-es | `00000000002554` | Rinderbraten | energy 268 kcal, macros give 121 kcal |
| food-fi | `00000020010911` | Gin Long Drink Cranberry Karpalolonkero | energy 56 kcal, macros give 26 kcal |
| food-fi | `00000020047559` | Yogurt Greek Style | energy 96 kcal, macros give 121 kcal |
| food-fr | `00000000000376` | All Natural Fibet | energy 60 kcal, macros give 81 kcal |
| food-fr | `00000000000406` | Francais | energy 25 kcal, macros give 405 kcal |
| food-gb | `00000000002523` | Peach | energy 38 kcal, macros give 75 kcal |
| food-gb | `00000000012126` | Passion fruit | energy 58 kcal, macros give 38 kcal |
| food-gr | `00000000021661` | apple | energy 50 kcal, macros give 4 kcal |
| food-gr | `00000020026158` | Melinzanosalata | energy 220 kcal, macros give 89 kcal |
| food-hr | `00000020121563` | Fajitas wrap kit | energy 128 kcal, macros give 240 kcal |
| food-hr | `00000020171841` | Roggen Vollkorn-Knäckebr | energy 373 kcal, macros give 287 kcal |
| food-hu | `00000020047559` | Yogurt Greek Style | energy 96 kcal, macros give 121 kcal |
| food-hu | `00000020093846` | Pulyka Mellhús Sajttal Töltött | energy 240 kcal, macros give 172 kcal |
| food-ie | `00000000000222` | Ultimate Daily Greens | energy 278 kcal, macros give 367 kcal |
| food-ie | `00000000002271` | 4 petits carrés | energy 507 kcal, macros give 328 kcal |
| food-il | `00000024476973` | Milk chocolate with raisins | energy 508 kcal, macros give 271 kcal |
| food-il | `00000080854753` | mentos clean breath | energy 239 kcal, macros give 392 kcal |
| food-in | `00000000027687` | Safawi dates | energy 0 kcal, macros give 330 kcal |
| food-in | `00000000630399` | Organic Spicy Avocado Hummus | energy 8 kcal, macros give 44 kcal |
| food-it | `00000000000031` | Start- sport eleven | energy 373 kcal, macros give 206 kcal |
| food-it | `00000000003469` | Strolghino di prosciutto | energy 272 kcal, macros give 355 kcal |
| food-jp | `00000045121685` | シナモン (カシア) | energy 243 kcal, macros give 136 kcal |
| food-jp | `00000045121739` | ターメリック | energy 312 kcal, macros give 382 kcal |
| food-lt | `00000003121009` | Peanut butter | energy 448 kcal, macros give 324 kcal |
| food-lt | `00000020094508` | Crefee mit feinen Kräutern | energy 163 kcal, macros give 243 kcal |
| food-lu | `00000009635654` | Chicorée soluble | energy 316 kcal, macros give 252 kcal |
| food-lu | `00000010453889` | Franzikaner | energy 110 kcal, macros give 30 kcal |
| food-ma | `00000000997805` | STIR FRY TERIYAKI | energy 100 kcal, macros give 132 kcal |
| food-ma | `00000010680988` | Amandes grillées et salées | energy 643 kcal, macros give 255 kcal |
| food-mx | `00000071303154` | Corned Beef | energy 499 kcal, macros give 298 kcal |
| food-mx | `00000075004132` | Beer | energy 31 kcal, macros give 8 kcal |
| food-nl | `00000000461610` | High premium hondenbrokken | energy 236 kcal, macros give 157 kcal |
| food-nl | `00000000808910` | Schuursponzen | energy 186 kcal, macros give 374 kcal |
| food-no | `00000042069775` | extra white | energy 160 kcal, macros give 260 kcal |
| food-no | `00000050173679` | Tyggis | energy 146 kcal, macros give 244 kcal |
| food-nz | `00000004632276` | Sour Cream & Chives Rice Crackers | energy 111 kcal, macros give 332 kcal |
| food-nz | `00000011369585` | Kombucha | energy 10 kcal, macros give 30 kcal |
| food-pl | `00000000228978` | Szynka & jajko | energy 132 kcal, macros give 105 kcal |
| food-pl | `00000020077242` | Baton musli jabłko | energy 176 kcal, macros give 460 kcal |
| food-pt | `00000020009755` | Altramuces | energy 106 kcal, macros give 82 kcal |
| food-pt | `00000020026394` | Bohnen weiß eingelegt in Tomatensoße | energy 142 kcal, macros give 316 kcal |
| food-ro | `00000007526008` | Bere neagră premium | energy 58 kcal, macros give 20 kcal |
| food-ro | `00000015783066` | Castraveți murați | energy 55 kcal, macros give 11 kcal |
| food-ru | `00000006257064` | Шоколад. Неглазированный протеиновый батончик | energy 295 kcal, macros give 235 kcal |
| food-ru | `00000012464814` | Halva | energy 1 kcal, macros give 46 kcal |
| food-sa | `00000090474064` | Red bull curuba - elderflower flavor energy drink | energy 457 kcal, macros give 44 kcal |
| food-sa | `00000090474675` | Red bull peach flavor energy drink | energy 455 kcal, macros give 44 kcal |
| food-se | `00000005557653` | Linfrö mjöl | energy 319 kcal, macros give 255 kcal |
| food-se | `00000013050962` | Marabou premium | energy 131 kcal, macros give 703 kcal |
| food-sg | `00000000263177` | Sainsbury peach and nectarine frozen | energy 42 kcal, macros give 85 kcal |
| food-sg | `00000000269919` | Cod in parsley sauce | energy 319 kcal, macros give 75 kcal |
| food-sk | `00000020320003` | SInečnicové jadierka (lúpané, pražené, solené) | energy 847 kcal, macros give 630 kcal |
| food-sk | `00000020544577` | Kabanosy | energy 379 kcal, macros give 491 kcal |
| food-th | `00000024765848` | Salat-Fein Garten-Kräuter | energy 214 kcal, macros give 158 kcal |
| food-th | `00000088124971` | COLIN the CATERPILLAR | energy 342 kcal, macros give 193 kcal |
| food-tr | `00000057030890` | Olips Mini Mints Nane Sert Şeker 12,5 G | energy 235 kcal, macros give 388 kcal |
| food-tr | `00000080785545` | Vivident | energy 126 kcal, macros give 250 kcal |
| food-ua | `00000042123880` | Orbit Blueberry x10 14g Sugar Free | energy 168 kcal, macros give 281 kcal |
| food-ua | `00646670541384` | Organic Super Greens | energy 35 kcal, macros give 9 kcal |
| food-us | `00000000001250` | Bismarckheringe 3,00 kg Kübel | energy 176 kcal, macros give 356 kcal |
| food-us | `00000000007122` | Test | energy 373 kcal, macros give 0 kcal |
| food-za | `00000029427369` | Organic Seedless Grapes | energy 294 kcal, macros give 68 kcal |
| food-za | `00000042102021` | Orbit Professional strong mint & menthol flavored chewing gum | energy 144 kcal, macros give 240 kcal |

## Spot checks

The most-scanned products in each country (`spotchecks/<country>.json`), looked up by barcode and by name, with the per-100 values of their source record.

| Pack | Products | By barcode | By name | Values | Passed |
|---|---|---|---|---|---|
| food-ar | 20 | 20 | 20 | 20 | 20 |
| food-at | 20 | 20 | 20 | 20 | 20 |
| food-au | 20 | 20 | 20 | 20 | 20 |
| food-be | 20 | 20 | 20 | 20 | 20 |
| food-bg | 20 | 20 | 20 | 20 | 20 |
| food-br | 20 | 20 | 20 | 20 | 20 |
| food-ca | 20 | 20 | 20 | 20 | 20 |
| food-ch | 20 | 20 | 20 | 20 | 20 |
| food-cz | 20 | 20 | 20 | 20 | 20 |
| food-de | 20 | 20 | 20 | 20 | 20 |
| food-dk | 20 | 20 | 20 | 20 | 20 |
| food-ee | 20 | 20 | 20 | 20 | 20 |
| food-es | 20 | 20 | 20 | 20 | 20 |
| food-fi | 20 | 20 | 20 | 20 | 20 |
| food-fr | 20 | 20 | 20 | 20 | 20 |
| food-gb | 20 | 20 | 20 | 20 | 20 |
| food-gr | 20 | 20 | 20 | 20 | 20 |
| food-hr | 20 | 20 | 20 | 20 | 20 |
| food-hu | 20 | 20 | 20 | 20 | 20 |
| food-ie | 20 | 20 | 20 | 20 | 20 |
| food-il | 20 | 20 | 20 | 20 | 20 |
| food-in | 20 | 20 | 20 | 20 | 20 |
| food-it | 20 | 20 | 20 | 20 | 20 |
| food-jp | 20 | 20 | 20 | 20 | 20 |
| food-lt | 20 | 20 | 20 | 20 | 20 |
| food-lu | 20 | 20 | 20 | 20 | 20 |
| food-ma | 20 | 20 | 20 | 20 | 20 |
| food-mx | 20 | 20 | 20 | 20 | 20 |
| food-nl | 20 | 20 | 20 | 20 | 20 |
| food-no | 20 | 20 | 20 | 20 | 20 |
| food-nz | 20 | 20 | 20 | 20 | 20 |
| food-pl | 20 | 20 | 20 | 20 | 20 |
| food-pt | 20 | 20 | 20 | 20 | 20 |
| food-ro | 20 | 20 | 20 | 20 | 20 |
| food-ru | 20 | 20 | 20 | 20 | 20 |
| food-sa | 20 | 20 | 20 | 20 | 20 |
| food-se | 20 | 20 | 20 | 20 | 20 |
| food-sg | 20 | 20 | 20 | 20 | 20 |
| food-sk | 20 | 20 | 20 | 20 | 20 |
| food-th | 20 | 20 | 20 | 20 | 20 |
| food-tr | 20 | 20 | 20 | 20 | 20 |
| food-ua | 20 | 20 | 20 | 20 | 20 |
| food-us | 20 | 20 | 20 | 20 | 20 |
| food-za | 20 | 20 | 20 | 20 | 20 |

## Pack threshold (Q5)

Products per country with energy, a valid barcode and a name or brand, before validation. Sizes are estimated at 232 bytes per product, the average of the packs built above. Downloads are about 37% of the size.

| At least | Countries | Products | Estimated size |
|---|---|---|---|
| 1,000 | 83 | 3,481,113 | 808.3 MB |
| 2,000 | 62 | 3,451,294 | 801.4 MB |
| 5,000 | 44 | 3,390,577 | 787.3 MB |
| 10,000 | 27 | 3,271,216 | 759.6 MB |
| 20,000 | 16 | 3,103,541 | 720.7 MB |

**Threshold:** 5,000 products (Q5): 44 countries over it.

Over the threshold without a pack: none.
