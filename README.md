# gamba-pipeline

Builds the food and exercise data for Gamba, a calorie and gym tracker for iPhone and iPad:

- `reference.sqlite`, bundled in the app: USDA generic foods with servings, and the exercise library.
- One pack per country, `food-<country>/pack.sqlite`: Open Food Facts products (plus USDA Branded Foods for the US), delivered on demand.

## Running it

```bash
uv run gamba-pipeline download    # fetch and verify every pinned input (inputs.toml)
uv run gamba-pipeline reference   # build build/reference.sqlite
uv run gamba-pipeline packs       # build build/packs/food-<country>/pack.sqlite for every country in countries.py
uv run gamba-pipeline package     # package each pack for Background Assets (needs Xcode 27)
uv run gamba-pipeline survey      # count each country's products (for the pack threshold)
uv run gamba-pipeline spotcheck   # check the packs against spotchecks/<country>.json
uv run gamba-pipeline report      # write build/REPORT.md, and the full lists to build/report/
uv run gamba-pipeline pin-latest  # pin the newest Open Food Facts export in inputs.toml
uv run gamba-pipeline release     # gzip each pack into build/release/, with the release notes
uv run gamba-pipeline upload      # upload the packs to App Store Connect (--dry-run lists them)
uv run gamba-pipeline review      # submit up to ten new pack versions for App Store review
uv run pytest -q
```

## Monthly run

The `Packs` workflow (`.github/workflows/packs.yml`) runs on the 1st of each month on GitHub's
`xcode-27` macOS runner. It pins the newest Open Food Facts export, builds and packages every pack,
spot-checks them against the new export and writes the report into the run's summary. What happens
next depends on the delivery mode: the workflow's input when it's run by hand, otherwise the
repository variable `PACK_DELIVERY`.

| Mode | |
|---|---|
| `dry-run` (the default) | Nothing leaves the runner; the report is kept as the run's artifact. |
| `testflight` | Uploads every pack to App Store Connect and waits until Apple has processed it (internal TestFlight uses the newest processed versions), then commits the new pins, spot checks and report and publishes the packs as a release, `packs-<date>`. |
| `app-store` | As `testflight`; then the new versions go to App Store review. Apple takes at most ten packs in a submission and reviews one submission without an app version at a time, so this run submits the first ten, and the daily `Review packs` workflow (`review.yml`) submits the next ten whenever the app has no review submission open. |

A failed spot check stops the run before anything is uploaded. A pack that fails to upload or
process doesn't stop the others, but then the run fails and commits, publishes and submits
nothing; the daily review still submits the packs that did process, and the failed one keeps its
last version.

Uploading needs an App Store Connect API key with the App Manager role, in the repository's
secrets `ASC_KEY_ID`, `ASC_ISSUER_ID` and `ASC_PRIVATE_KEY` (the `.p8` file's contents). Run by
hand, `upload` reads the same three environment variables. The USDA and free-exercise-db pins move
by hand.

## Sources

| Source | License |
|---|---|
| [USDA FoodData Central](https://fdc.nal.usda.gov/) Foundation Foods and SR Legacy | Public domain (CC0) |
| [free-exercise-db](https://github.com/yuhonas/free-exercise-db) | Public domain (Unlicense) |
| [Open Food Facts](https://world.openfoodfacts.org/) (packs) | ODbL |
| [USDA FoodData Central](https://fdc.nal.usda.gov/) Branded Foods (the US pack) | Public domain (CC0) |

## License

The code is [MIT](LICENSE). The packs are ODbL, with Open Food Facts' contents under DbCL, and
`reference.sqlite` is public domain: see [DATA-LICENSE.md](DATA-LICENSE.md).

## Results

### Reference database

`uv run gamba-pipeline reference --build-date 2026-10-14` (inputs pinned in `inputs.toml`; schema 1.1):

| | |
|---|---|
| Foods | 8,032 (Foundation 329, SR Legacy 7,703) |
| Rejected / duplicate names / flagged / carbs set to 0 g | 91 / 139 / 142 / 10 |
| Exercises | 739 (weightReps 605, bodyweightReps 123, duration 10, assisted 1); 66 short names differ from the name |
| Size | 2.5 MB; two builds are byte-identical |

Exercise names are in Apple's title case, and each has a short name for tight spaces such as the Live Activity: without a leading “Barbell”, the variant after “ - ” and anything in parentheses (a “With Bands” variant becomes “Band” in front). `overrides/exercise_overrides.json` corrects the exceptions by exercise ID, with `name`, `trackingType` and `shortName`; `build/reference.report.json` lists every short name that differs.

### Packs

`uv run gamba-pipeline packs --build-date 2026-10-18` (Open Food Facts export `3dc10b5`, USDA Branded 2026-04-30) builds a pack for each of the 44 countries with at least 5,000 products (`countries.py`), with names in each country's official languages plus English:

| | |
|---|---|
| Packs | 44, from food-fr (883,730 products, 193.8 MB) and food-us (849,773, 215.6 MB, USDA nutrients for 109,682) down to food-ua (5,104, 1.4 MB) |
| Products | 3,456,741 (rejected 26,695, flagged 148,951) |
| Size | 802.7 MB; 296.2 MB to download, packaged |
| Spot checks | 20 per pack, all passed |
| Build | about 7½ minutes and 3.2 GB of memory on an M1 Pro; two builds are byte-identical |

Every pack is in `build/REPORT.md`. Names written without spaces (Japanese, Chinese, Thai) are one word each to the search index, so searching them finds a name by its start only.
