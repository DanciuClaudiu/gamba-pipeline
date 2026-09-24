"""Asset-pack archives for Background Assets (SPEC §10 step 5, PLAN §2.13): one on-demand pack per
country, holding food-<country>/pack.sqlite. Uploading them to App Store Connect is M9."""

import json
import subprocess
from pathlib import Path


def manifest(pack_id: str) -> dict:
    """The ba-package manifest. Paths resolve against the manifest's own folder (sourceRoot)."""
    return {
        "assetPackID": pack_id,
        "downloadPolicy": {"onDemand": {}},
        "fileSelectors": [{"directory": pack_id}],
        "platforms": ["iOS"],
        "sourceRoot": ".",
    }


def write_manifest(packs_dir: Path, pack_id: str) -> Path:
    path = packs_dir / f"Manifest-{pack_id}.json"
    path.write_text(json.dumps(manifest(pack_id), indent=2) + "\n", encoding="utf-8")
    return path


def package(packs_dir: Path, pack_id: str, output_dir: Path) -> Path:
    """Runs `xcrun ba-package` (Xcode 27) and returns the archive's path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"{pack_id}.aar"
    archive.unlink(missing_ok=True)
    subprocess.run(
        [
            "xcrun", "ba-package", "package", str(write_manifest(packs_dir, pack_id)),
            "--output-path", str(archive), "--quiet",
        ],
        check=True,
    )  # fmt: skip
    return archive
