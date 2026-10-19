"""The `upload` command: every archive in build/packages goes to App Store Connect, the run waits
until Apple has processed each one, and with `--submit` the new versions go to App Store review
in one submission. A pack that fails doesn't stop the others, but then nothing is submitted."""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from gamba_pipeline.appstore import BUNDLE_ID, AppStoreError, Version

FINAL = ("COMPLETE", "FAILED")


class Client(Protocol):
    def app_id(self, bundle_id: str = BUNDLE_ID) -> str: ...
    def asset_id(self, app_id: str, pack_id: str) -> str: ...
    def latest_version(self, asset_id: str) -> Version | None: ...
    def upload(self, archive: Path, app_id: str) -> None: ...
    def open_submission(self, app_id: str) -> str | None: ...
    def submit(self, app_id: str, version_ids: list[str]) -> str: ...


def megabytes(size: int) -> str:
    return f"{size / 1_000_000:.1f} MB"


def deliver(
    packages: Path,
    client: Client | None,
    *,
    submit: bool = False,
    dry_run: bool = False,
    out: Callable[[str], None] = print,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    timeout: float = 3 * 3600,
    interval: float = 60,
) -> int:
    archives = sorted(packages.glob("food-*.aar"))
    if not archives:
        out(f"no archives in {packages}; run package first")
        return 1
    if dry_run or client is None:
        for archive in archives:
            out(f"{archive.name}  {megabytes(archive.stat().st_size)}")
        total = megabytes(sum(archive.stat().st_size for archive in archives))
        review = ", and submit them for App Store review" if submit else ""
        out(f"would upload {len(archives)} packs ({total}) to {BUNDLE_ID}{review}")
        return 0

    app = client.app_id()
    pending: dict[str, tuple[str, str | None]] = {}
    for archive in archives:
        pack = archive.stem
        asset = client.asset_id(app, pack)
        before = client.latest_version(asset)
        try:
            client.upload(archive, app)
        except AppStoreError as error:
            out(f"{pack}: upload failed: {error}")
            continue
        out(f"{pack}: uploaded")
        pending[pack] = (asset, before.version if before else None)

    processed: dict[str, Version] = {}
    start = clock()
    while pending:
        for pack, (asset, before) in list(pending.items()):
            version = client.latest_version(asset)
            if version is None or version.version == before or version.state not in FINAL:
                continue
            del pending[pack]
            if version.state == "COMPLETE":
                processed[pack] = version
                out(f"{pack}: version {version.version} complete")
            else:
                reason = "; ".join(version.errors) or "no reason given"
                out(f"{pack}: version {version.version} failed: {reason}")
        if not pending:
            break
        if clock() - start >= timeout:
            for pack in pending:
                out(f"{pack}: still processing after {timeout / 3600:g} h")
            break
        sleep(interval)

    out(f"{len(processed)} of {len(archives)} packs processed")
    if len(processed) < len(archives):
        return 1
    if submit:
        if client.open_submission(app):
            out(
                "a review submission is already open in App Store Connect; submit the packs "
                "there, or remove it and run this again"
            )
            return 1
        submission = client.submit(app, [processed[pack].id for pack in sorted(processed)])
        out(f"submitted {len(processed)} packs for App Store review ({submission})")
    return 0
