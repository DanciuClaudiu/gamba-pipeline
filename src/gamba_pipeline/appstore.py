"""App Store Connect for the packs (SPEC §10 step 5): `xcrun altool --upload-asset-pack` uploads
each archive, and App Store Connect's API, with the same key, does what altool doesn't: finding
the app, creating a pack's record the first time, reading processing states and submitting the
new versions for review. The API's tokens come from `altool --generate-jwt`, which signs offline."""

import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

API = "https://api.appstoreconnect.apple.com"
BUNDLE_ID = "com.danciuclaudiu.gamba"  # SPEC §11
TOKEN_LIFETIME = 15 * 60  # altool's tokens last 20 minutes
RETRY_WAITS = (2, 4, 8, 16)
JWT = re.compile(r"[\w-]+\.[\w-]+\.[\w-]+")
ENV = ("ASC_KEY_ID", "ASC_ISSUER_ID", "ASC_PRIVATE_KEY")
OPEN_SUBMISSION = (
    "READY_FOR_REVIEW", "WAITING_FOR_REVIEW", "IN_REVIEW", "UNRESOLVED_ISSUES",
    "CANCELING", "COMPLETING",
)  # fmt: skip

Send = Callable[[str, str, dict[str, str], bytes | None], tuple[int, bytes]]


class AppStoreError(Exception):
    """App Store Connect or altool refused a request."""


@dataclass(frozen=True)
class Credentials:
    """An App Store Connect API key, its `.p8` file in `keys_dir` where altool looks for it."""

    key_id: str
    issuer_id: str
    keys_dir: Path

    @property
    def key_path(self) -> Path:
        return self.keys_dir / f"AuthKey_{self.key_id}.p8"

    @classmethod
    def from_env(cls, env: Mapping[str, str], keys_dir: Path) -> "Credentials":
        missing = [name for name in ENV if not env.get(name)]
        if missing:
            raise SystemExit(f"set {', '.join(missing)} (the App Store Connect API key, PLAN §4.7)")
        credentials = cls(env["ASC_KEY_ID"], env["ASC_ISSUER_ID"], keys_dir)
        keys_dir.mkdir(parents=True, exist_ok=True)
        key = env["ASC_PRIVATE_KEY"]
        path = credentials.key_path
        path.touch(mode=0o600)
        path.chmod(0o600)
        path.write_text(key if key.endswith("\n") else key + "\n", encoding="utf-8")
        return credentials


@dataclass(frozen=True)
class Version:
    """A background asset version: `state` is AWAITING_UPLOAD, PROCESSING, FAILED or COMPLETE;
    `release` is its App Store release's state (PREPARE_FOR_SUBMISSION … READY_FOR_DISTRIBUTION,
    REJECTED, SUPERSEDED), None before it has one."""

    id: str
    version: str
    state: str
    errors: tuple[str, ...]
    release: str | None = None

    @classmethod
    def from_resource(cls, resource: dict, releases: Mapping[str, str]) -> "Version":
        attributes = resource["attributes"]
        details = attributes.get("stateDetails") or {}
        errors = tuple(error.get("description", "") for error in details.get("errors") or [])
        link = ((resource.get("relationships") or {}).get("appStoreRelease") or {}).get("data")
        release = releases.get(link["id"]) if link else None
        return cls(resource["id"], attributes["version"], attributes["state"], errors, release)


def _send(method: str, url: str, headers: dict[str, str], body: bytes | None) -> tuple[int, bytes]:
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def _query(**params: str) -> str:
    return urllib.parse.urlencode(params, safe="[],")


class AppStoreConnect:
    def __init__(
        self,
        credentials: Credentials,
        run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
        send: Send = _send,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.credentials = credentials
        self._run, self._send, self._clock, self._sleep = run, send, clock, sleep
        self._token: tuple[str, float] | None = None

    def _altool(self, args: list[str], env: Mapping[str, str] | None = None) -> str:
        result = self._run(["xcrun", "altool", *args], capture_output=True, text=True, env=env)
        output = (result.stdout or "") + (result.stderr or "")
        if result.returncode != 0:
            raise AppStoreError(f"altool {args[0]}: {output.strip()}")
        return output

    @property
    def _key(self) -> list[str]:
        return ["--api-key", self.credentials.key_id, "--api-issuer", self.credentials.issuer_id]

    def token(self) -> str:
        if self._token is None or self._clock() - self._token[1] >= TOKEN_LIFETIME:
            output = self._altool(
                ["--generate-jwt", *self._key, "--p8-file-path", str(self.credentials.key_path)]
            )
            tokens = [line.strip() for line in output.splitlines() if JWT.fullmatch(line.strip())]
            if not tokens:
                raise AppStoreError(f"altool --generate-jwt printed no token: {output.strip()}")
            self._token = (tokens[-1], self._clock())
        return self._token[0]

    def request(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        for attempt in range(len(RETRY_WAITS) + 1):
            headers = {
                "Authorization": f"Bearer {self.token()}",
                "Content-Type": "application/json",
            }
            status, payload = self._send(method, API + path, headers, data)
            if (status == 429 or status >= 500) and attempt < len(RETRY_WAITS):
                self._sleep(RETRY_WAITS[attempt])
                continue
            break
        try:
            parsed = json.loads(payload) if payload else {}
        except ValueError:
            parsed = {}
        if not 200 <= status < 300:
            details = "; ".join(
                error.get("detail") or error.get("title", "") for error in parsed.get("errors", [])
            )
            raise AppStoreError(f"{method} {path}: {status} {details}".rstrip())
        return parsed

    def app_id(self, bundle_id: str = BUNDLE_ID) -> str:
        apps = self.request("GET", f"/v1/apps?{_query(**{'filter[bundleId]': bundle_id})}")
        for app in apps["data"]:
            if app["attributes"]["bundleId"] == bundle_id:
                return app["id"]
        raise AppStoreError(f"no app with bundle ID {bundle_id} in App Store Connect")

    def asset_id(self, app_id: str, pack_id: str) -> str:
        query = _query(**{"filter[assetPackIdentifier]": pack_id})
        found = self.request("GET", f"/v1/apps/{app_id}/backgroundAssets?{query}")["data"]
        if found:
            return found[0]["id"]
        created = self.request(
            "POST",
            "/v1/backgroundAssets",
            {
                "data": {
                    "type": "backgroundAssets",
                    "attributes": {"assetPackIdentifier": pack_id},
                    "relationships": {"app": {"data": {"type": "apps", "id": app_id}}},
                }
            },
        )
        return created["data"]["id"]

    def assets(self, app_id: str) -> list[tuple[str, str]]:
        """The app's asset packs that aren't archived, as (record ID, pack ID), by pack ID."""
        query = _query(sort="assetPackIdentifier", limit="200")
        found = self.request("GET", f"/v1/apps/{app_id}/backgroundAssets?{query}")["data"]
        return [
            (asset["id"], asset["attributes"]["assetPackIdentifier"])
            for asset in found
            if not asset["attributes"].get("archived")
        ]

    def latest_version(self, asset_id: str) -> Version | None:
        query = _query(sort="-version", limit="1", include="appStoreRelease")
        answer = self.request("GET", f"/v1/backgroundAssets/{asset_id}/versions?{query}")
        releases = {
            item["id"]: item["attributes"]["state"]
            for item in answer.get("included", [])
            if item["type"] == "backgroundAssetVersionAppStoreReleases"
        }
        versions = answer["data"]
        return Version.from_resource(versions[0], releases) if versions else None

    def upload(self, archive: Path, app_id: str) -> None:
        env = {**os.environ, "API_PRIVATE_KEYS_DIR": str(self.credentials.keys_dir)}
        self._altool(["--upload-asset-pack", str(archive), "--apple-id", app_id, *self._key], env)

    def open_submission(self, app_id: str) -> tuple[str, str] | None:
        """A review submission of the app's that isn't complete, as (ID, state): a draft, one
        waiting for or in review, or one with unresolved issues."""
        query = _query(
            **{
                "filter[app]": app_id,
                "filter[platform]": "IOS",
                "filter[state]": ",".join(OPEN_SUBMISSION),
            }
        )
        found = self.request("GET", f"/v1/reviewSubmissions?{query}")["data"]
        return (found[0]["id"], found[0]["attributes"]["state"]) if found else None

    def submit(self, app_id: str, version_ids: list[str]) -> str:
        submission = self.request(
            "POST",
            "/v1/reviewSubmissions",
            {
                "data": {
                    "type": "reviewSubmissions",
                    "attributes": {"platform": "IOS"},
                    "relationships": {"app": {"data": {"type": "apps", "id": app_id}}},
                }
            },
        )["data"]["id"]
        for version_id in version_ids:
            self.request(
                "POST",
                "/v1/reviewSubmissionItems",
                {
                    "data": {
                        "type": "reviewSubmissionItems",
                        "relationships": {
                            "reviewSubmission": {
                                "data": {"type": "reviewSubmissions", "id": submission}
                            },
                            "backgroundAssetVersion": {
                                "data": {"type": "backgroundAssetVersions", "id": version_id}
                            },
                        },
                    }
                },
            )
        self.request(
            "PATCH",
            f"/v1/reviewSubmissions/{submission}",
            {
                "data": {
                    "type": "reviewSubmissions",
                    "id": submission,
                    "attributes": {"submitted": True},
                }
            },
        )
        return submission
