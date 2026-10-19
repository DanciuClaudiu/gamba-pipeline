from pathlib import Path

import pytest

from gamba_pipeline import delivery
from gamba_pipeline.appstore import AppStoreError, Version


def v(number: int, state: str, *errors: str) -> Version:
    return Version(f"v{number}", str(number), state, errors)


class FakeClient:
    """App Store Connect as delivery sees it. Each pack's versions play back one per call to
    `latest_version`, and the last one repeats."""

    def __init__(self, versions, fail_uploads=(), open_submission=None):
        self.versions = {pack: list(queue) for pack, queue in versions.items()}
        self.fail_uploads = set(fail_uploads)
        self.open = open_submission
        self.uploads: list[str] = []
        self.submitted: list[str] | None = None

    def app_id(self, bundle_id="com.danciuclaudiu.gamba"):
        return "app1"

    def asset_id(self, app_id, pack_id):
        return f"asset-{pack_id}"

    def latest_version(self, asset_id):
        queue = self.versions[asset_id.removeprefix("asset-")]
        return queue.pop(0) if len(queue) > 1 else queue[0]

    def upload(self, archive, app_id):
        self.uploads.append(archive.name)
        if archive.stem in self.fail_uploads:
            raise AppStoreError("altool --upload-asset-pack: 400 invalid values")

    def open_submission(self, app_id):
        return self.open

    def submit(self, app_id, version_ids):
        self.submitted = version_ids
        return "sub1"


def archives(tmp_path: Path, **sizes: int) -> Path:
    packages = tmp_path / "packages"
    packages.mkdir()
    for pack, size in sizes.items():
        (packages / f"food-{pack}.aar").write_bytes(b"\0" * size)
    return packages


def run(packages, client, **options):
    lines, sleeps = [], []
    code = delivery.deliver(packages, client, out=lines.append, sleep=sleeps.append, **options)
    return code, lines, sleeps


def test_dry_run_lists_the_archives(tmp_path):
    packages = archives(tmp_path, gb=1_000_000, ar=600_000)
    code, lines, _ = run(packages, None, dry_run=True)
    assert code == 0
    assert lines == [
        "food-ar.aar  0.6 MB",
        "food-gb.aar  1.0 MB",
        "would upload 2 packs (1.6 MB) to com.danciuclaudiu.gamba",
    ]
    _, lines, _ = run(packages, None, dry_run=True, submit=True)
    assert lines[-1] == (
        "would upload 2 packs (1.6 MB) to com.danciuclaudiu.gamba, "
        "and submit them for App Store review"
    )


def test_no_archives(tmp_path):
    code, lines, _ = run(archives(tmp_path), FakeClient({}))
    assert code == 1
    assert lines[0].startswith("no archives in ") and lines[0].endswith("; run package first")


def test_uploads_every_pack_and_waits_for_processing(tmp_path):
    client = FakeClient(
        {
            "food-ro": [v(2, "COMPLETE"), v(3, "PROCESSING"), v(3, "COMPLETE")],
            "food-gb": [None, v(1, "COMPLETE")],
        }
    )
    code, lines, sleeps = run(archives(tmp_path, ro=10, gb=10), client)
    assert code == 0
    assert client.uploads == ["food-gb.aar", "food-ro.aar"]
    assert sleeps == [60]
    assert lines == [
        "food-gb: uploaded",
        "food-ro: uploaded",
        "food-gb: version 1 complete",
        "food-ro: version 3 complete",
        "2 of 2 packs processed",
    ]
    assert client.submitted is None


def test_waits_for_the_new_version(tmp_path):
    client = FakeClient({"food-ro": [v(2, "COMPLETE"), v(2, "COMPLETE"), v(3, "COMPLETE")]})
    code, lines, sleeps = run(archives(tmp_path, ro=10), client)
    assert code == 0 and sleeps == [60]
    assert "food-ro: version 3 complete" in lines


def test_submits_the_new_versions(tmp_path):
    client = FakeClient(
        {"food-ro": [v(2, "COMPLETE"), v(3, "COMPLETE")], "food-gb": [None, v(1, "COMPLETE")]}
    )
    code, lines, _ = run(archives(tmp_path, ro=10, gb=10), client, submit=True)
    assert code == 0
    assert client.submitted == ["v1", "v3"]
    assert lines[-1] == "submitted 2 packs for App Store review (sub1)"


def test_a_failed_upload_doesnt_stop_the_others(tmp_path):
    versions = {"food-gb": [None], "food-ro": [v(2, "COMPLETE"), v(3, "COMPLETE")]}
    client = FakeClient(versions, fail_uploads={"food-gb"})
    code, lines, _ = run(archives(tmp_path, ro=10, gb=10), client, submit=True)
    assert code == 1
    assert client.uploads == ["food-gb.aar", "food-ro.aar"]
    assert "food-gb: upload failed: altool --upload-asset-pack: 400 invalid values" in lines
    assert "1 of 2 packs processed" in lines
    assert client.submitted is None


def test_nothing_is_submitted_when_a_pack_fails_processing(tmp_path):
    client = FakeClient({"food-ro": [v(2, "COMPLETE"), v(3, "FAILED", "Invalid manifest")]})
    code, lines, _ = run(archives(tmp_path, ro=10), client, submit=True)
    assert code == 1
    assert "food-ro: version 3 failed: Invalid manifest" in lines
    assert client.submitted is None


def test_leaves_an_open_review_submission_alone(tmp_path):
    client = FakeClient({"food-ro": [v(2, "COMPLETE"), v(3, "COMPLETE")]}, open_submission="s9")
    code, lines, _ = run(archives(tmp_path, ro=10), client, submit=True)
    assert code == 1
    assert client.submitted is None
    assert lines[-1] == (
        "a review submission is already open in App Store Connect; submit the packs there, "
        "or remove it and run this again"
    )


def test_gives_up_waiting_after_the_timeout(tmp_path):
    now = [0.0]

    def sleep(seconds):
        now[0] += seconds

    client = FakeClient({"food-ro": [v(2, "COMPLETE"), v(3, "PROCESSING")]})
    lines = []
    code = delivery.deliver(
        archives(tmp_path, ro=10), client, out=lines.append, sleep=sleep, clock=lambda: now[0]
    )
    assert code == 1
    assert now[0] == 3 * 3600
    assert lines[-2:] == ["food-ro: still processing after 3 h", "0 of 1 packs processed"]


def test_the_upload_command_dry_runs_without_credentials(tmp_path, monkeypatch, capsys):
    from gamba_pipeline import cli

    (tmp_path / "inputs.toml").write_bytes((Path(__file__).parents[1] / "inputs.toml").read_bytes())
    (tmp_path / "build").mkdir()
    archives(tmp_path / "build", ro=600_000)
    for name in ("ASC_KEY_ID", "ASC_ISSUER_ID", "ASC_PRIVATE_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    assert cli.main(["upload", "--dry-run"]) == 0
    assert capsys.readouterr().out.splitlines()[-1] == (
        "would upload 1 packs (0.6 MB) to com.danciuclaudiu.gamba"
    )
    with pytest.raises(SystemExit, match="ASC_KEY_ID, ASC_ISSUER_ID, ASC_PRIVATE_KEY"):
        cli.main(["upload"])
