"""The monthly release (SPEC §10 step 7): each pack gzipped as `food-<country>.sqlite.gz`, with
notes crediting its sources, for the run to publish on GitHub under the ODbL."""

import gzip
import shutil
from pathlib import Path

from gamba_pipeline.inputs import Input

REPOSITORY = "https://github.com/DanciuClaudiu/gamba-pipeline"


def gzip_file(source: Path, target: Path) -> None:
    """Level 9 with no file name or time stored, so the same pack gives the same bytes."""
    with (
        source.open("rb") as raw,
        target.open("wb") as out,
        gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=out, mtime=0) as gz,
    ):
        shutil.copyfileobj(raw, gz, 1 << 20)


def notes(build_date: str, pinned: dict[str, Input], packs: int) -> str:
    count = f"{packs} pack{'' if packs == 1 else 's'}"
    export, branded = pinned["off"].release[:7], pinned["branded"].release
    odbl = "https://opendatacommons.org/licenses/odbl/1-0/"
    dbcl = "https://opendatacommons.org/licenses/dbcl/1-0/"
    paragraphs = [
        f"Gamba's food packs, built {build_date} from Open Food Facts export `{export}` and, "
        f"for the US pack, USDA FoodData Central Branded Foods {branded}: {count}.",
        "Each file is one country's `pack.sqlite`, gzipped. `build/REPORT.md` at this "
        "release's commit has every pack's numbers and checks.",
        "The packs are derived from the Open Food Facts database, © Open Food Facts "
        f"contributors, and are available under the [Open Database License (ODbL) 1.0]({odbl}), "
        f"with the individual contents under the [Database Contents License (DbCL) 1.0]({dbcl}). "
        f"See [DATA-LICENSE.md]({REPOSITORY}/blob/main/DATA-LICENSE.md).",
        "USDA FoodData Central: U.S. Department of Agriculture, Agricultural Research "
        "Service. FoodData Central. https://fdc.nal.usda.gov.",
    ]
    return "\n\n".join(paragraphs) + "\n"


def write(build: Path, build_date: str, pinned: dict[str, Input]) -> list[Path]:
    """Writes build/release/ afresh and returns its files, the packs first."""
    folder = build / "release"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir(parents=True)
    written = []
    for pack in sorted(build.glob("packs/food-*/pack.sqlite")):
        target = folder / f"{pack.parent.name}.sqlite.gz"
        gzip_file(pack, target)
        written.append(target)
    path = folder / "NOTES.md"
    path.write_text(notes(build_date, pinned, len(written)), encoding="utf-8")
    return [*written, path]
