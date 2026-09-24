import json
import shutil
import subprocess

import pytest

from gamba_pipeline import package


def test_the_manifest_is_an_on_demand_ios_pack():
    assert package.manifest("food-ro") == {
        "assetPackID": "food-ro",
        "downloadPolicy": {"onDemand": {}},
        "fileSelectors": [{"directory": "food-ro"}],
        "platforms": ["iOS"],
        "sourceRoot": ".",
    }


def test_writes_the_manifest_next_to_the_packs(tmp_path):
    path = package.write_manifest(tmp_path, "food-ro")
    assert path == tmp_path / "Manifest-food-ro.json"
    assert json.loads(path.read_text(encoding="utf-8")) == package.manifest("food-ro")


def has_ba_package() -> bool:
    if shutil.which("xcrun") is None:
        return False
    return subprocess.run(["xcrun", "--find", "ba-package"], capture_output=True).returncode == 0


@pytest.mark.skipif(not has_ba_package(), reason="needs Xcode 27's ba-package")
def test_packages_a_pack(tmp_path):
    (tmp_path / "packs" / "food-zz").mkdir(parents=True)
    (tmp_path / "packs" / "food-zz" / "pack.sqlite").write_bytes(b"not really a database")
    archive = package.package(tmp_path / "packs", "food-zz", tmp_path / "packages")
    assert archive == tmp_path / "packages" / "food-zz.aar"
    assert archive.stat().st_size > 0
