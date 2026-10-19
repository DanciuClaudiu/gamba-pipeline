"""Getting the packs to devices. `upload` sends every archive in build/packages to App Store
Connect and waits until Apple has processed each one; a pack that fails doesn't stop the others.
`review` submits the processed versions that were never submitted, ten at a time (Apple's limit
per submission), and only when the app has no review submission open (Apple reviews one
submission without an app version at a time), so a daily run takes a month's packs through in
turn."""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from gamba_pipeline.appstore import BUNDLE_ID, AppStoreError, Version

FINAL = ("COMPLETE", "FAILED")
REVIEW_LIMIT = 10
UNSUBMITTED = (None, "PREPARE_FOR_SUBMISSION", "READY_FOR_REVIEW")


class Client(Protocol):
    def app_id(self, bundle_id: str = BUNDLE_ID) -> str: ...
    def asset_id(self, app_id: str, pack_id: str) -> str: ...
    def assets(self, app_id: str) -> list[tuple[str, str]]: ...
    def latest_version(self, asset_id: str) -> Version | None: ...
    def upload(self, archive: Path, app_id: str) -> None: ...
    def open_submission(self, app_id: str) -> tuple[str, str] | None: ...
    def submit(self, app_id: str, version_ids: list[str]) -> str: ...


def megabytes(size: int) -> str:
    return f"{size / 1_000_000:.1f} MB"


def deliver(
    packages: Path,
    client: Client | None,
    *,
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
        out(f"would upload {len(archives)} packs ({total}) to {BUNDLE_ID}")
        return 0

    app = client.app_id()
    pending: dict[str, tuple[str, str | None]] = {}
    for archive in archives:
        pack = archive.stem
        try:
            asset = client.asset_id(app, pack)
            before = client.latest_version(asset)
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
    return 0 if len(processed) == len(archives) else 1


def review(client: Client, *, out: Callable[[str], None] = print, limit: int = REVIEW_LIMIT) -> int:
    """Submits up to `limit` pack versions that are processed and were never submitted."""
    app = client.app_id()
    open_submission = client.open_submission(app)
    if open_submission:
        state = open_submission[1].lower().replace("_", " ")
        out(f"a review submission is {state} in App Store Connect; the packs wait until it's done")
        return 0
    waiting = []
    for asset, pack in client.assets(app):
        version = client.latest_version(asset)
        if version and version.state == "COMPLETE" and version.release in UNSUBMITTED:
            waiting.append((pack, version))
    if not waiting:
        out("no new pack versions to submit")
        return 0
    batch = waiting[:limit]
    submission = client.submit(app, [version.id for _, version in batch])
    packs = ", ".join(pack for pack, _ in batch)
    out(f"submitted {len(batch)} packs for App Store review ({submission}): {packs}")
    if len(waiting) > limit:
        out(f"{len(waiting) - limit} more wait for the next submission")
    return 0
