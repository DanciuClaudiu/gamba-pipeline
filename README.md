# gamba-pipeline

Builds the food and exercise data for Gamba, a calorie and gym tracker for iPhone and iPad:

- `reference.sqlite`, bundled in the app: USDA generic foods with servings, and the exercise library.
- One pack per country (from Milestone 2.2): Open Food Facts products, delivered on demand.

## Running it

```bash
uv run gamba-pipeline download    # fetch and verify every pinned input (inputs.toml)
uv run gamba-pipeline reference   # build build/reference.sqlite
uv run pytest -q
```

## Sources

| Source | License |
|---|---|
| [USDA FoodData Central](https://fdc.nal.usda.gov/) Foundation Foods and SR Legacy | Public domain (CC0) |
| [free-exercise-db](https://github.com/yuhonas/free-exercise-db) | Public domain (Unlicense) |
| [Open Food Facts](https://world.openfoodfacts.org/) (packs, from Milestone 2.2) | ODbL |

This repository's own license is decided before the first packs are published (Q69).

## Results

`uv run gamba-pipeline reference --build-date 2026-09-24` (inputs pinned in `inputs.toml`):

| | |
|---|---|
| Foods | 8,032 (Foundation 329, SR Legacy 7,703) |
| Rejected / duplicate names / flagged / carbs set to 0 g | 91 / 139 / 142 / 10 |
| Exercises | 739 (weightReps 605, bodyweightReps 123, duration 10, assisted 1) |
| Size | 2.5 MB; two builds are byte-identical |
