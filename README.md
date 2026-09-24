# gamba-pipeline

Builds the food and exercise data for Gamba, a calorie and gym tracker for iPhone and iPad:

- `reference.sqlite`, bundled in the app: USDA generic foods with servings, and the exercise library.
- One pack per country, `food-<country>/pack.sqlite`: Open Food Facts products (plus USDA Branded Foods for the US), delivered on demand.

## Running it

```bash
uv run gamba-pipeline download    # fetch and verify every pinned input (inputs.toml)
uv run gamba-pipeline reference   # build build/reference.sqlite
uv run gamba-pipeline packs       # build build/packs/food-<country>/pack.sqlite for GB, RO and US
uv run pytest -q
```

## Sources

| Source | License |
|---|---|
| [USDA FoodData Central](https://fdc.nal.usda.gov/) Foundation Foods and SR Legacy | Public domain (CC0) |
| [free-exercise-db](https://github.com/yuhonas/free-exercise-db) | Public domain (Unlicense) |
| [Open Food Facts](https://world.openfoodfacts.org/) (packs) | ODbL |
| [USDA FoodData Central](https://fdc.nal.usda.gov/) Branded Foods (the US pack) | Public domain (CC0) |

This repository's own license is decided before the first packs are published (Q69).

## Results

### Reference database

`uv run gamba-pipeline reference --build-date 2026-09-24` (inputs pinned in `inputs.toml`):

| | |
|---|---|
| Foods | 8,032 (Foundation 329, SR Legacy 7,703) |
| Rejected / duplicate names / flagged / carbs set to 0 g | 91 / 139 / 142 / 10 |
| Exercises | 739 (weightReps 605, bodyweightReps 123, duration 10, assisted 1) |
| Size | 2.5 MB; two builds are byte-identical |

### Packs

`uv run gamba-pipeline packs --build-date 2026-09-24` (Open Food Facts export `3dc10b5`, USDA Branded 2026-04-30):

| Pack | Products | Size | Rejected | Flagged |
|---|---|---|---|---|
| food-gb | 149,156 | 35.1 MB | 359 | 5,178 |
| food-ro | 13,047 | 3.2 MB | 55 | 355 |
| food-us | 849,773 (USDA nutrients for 109,682) | 215.6 MB | 21,520 | 39,416 |

About 2 minutes for all three; two builds are byte-identical.
