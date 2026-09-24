# Data licenses

The code in this repository is MIT-licensed ([LICENSE](LICENSE)). The data it builds is licensed
by its sources:

| Output | Built from | License |
|---|---|---|
| Country packs, `food-<country>/pack.sqlite` | [Open Food Facts](https://world.openfoodfacts.org); for the US pack also [USDA FoodData Central](https://fdc.nal.usda.gov) Branded Foods | [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/), with the individual contents under the [Database Contents License (DbCL) 1.0](https://opendatacommons.org/licenses/dbcl/1-0/) |
| `reference.sqlite` | USDA FoodData Central Foundation Foods and SR Legacy; [free-exercise-db](https://github.com/yuhonas/free-exercise-db) | Public domain ([CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) and [the Unlicense](https://unlicense.org)) |

The packs are derived from the Open Food Facts database, © Open Food Facts contributors, which is
available under the ODbL; as the ODbL requires, they are offered under the same license. Each
pack's `meta` table records its license and attribution.

USDA FoodData Central: U.S. Department of Agriculture, Agricultural Research Service.
FoodData Central. https://fdc.nal.usda.gov.
