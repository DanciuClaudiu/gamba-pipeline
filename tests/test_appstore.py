import json
import stat
import subprocess
from pathlib import Path

import pytest

from gamba_pipeline import appstore

KEY = "-----BEGIN PRIVATE KEY-----\nMIGT\n-----END PRIVATE KEY-----\n"
TOKEN = "eyJhbGciOiJFUzI1NiJ9.eyJpc3MiOiJ4In0.c2lnbmF0dXJl"


class FakeApple:
    """App Store Connect's API: canned answers by (method, path), each used once, in order."""

    def __init__(self, answers: dict[tuple[str, str], list[tuple[int, dict]]]):
        self.answers = {key: list(value) for key, value in answers.items()}
        self.requests: list[tuple[str, str, dict, dict | None]] = []

    def __call__(self, method: str, url: str, headers: dict, body: bytes | None):
        path = url.removeprefix(appstore.API)
        self.requests.append((method, path, headers, json.loads(body) if body else None))
        status, payload = self.answers[(method, path)].pop(0)
        return status, json.dumps(payload).encode()


class FakeRun:
    """subprocess.run for altool: records each call and answers with `stdout`."""

    def __init__(self, stdout: str = f"Running altool at path '/x/altool'...\n\n{TOKEN}\n", code=0):
        self.stdout, self.code = stdout, code
        self.calls: list[tuple[list[str], dict]] = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, self.code, stdout=self.stdout, stderr="")


def credentials(tmp_path: Path) -> appstore.Credentials:
    env = {"ASC_KEY_ID": "KEY123", "ASC_ISSUER_ID": "issuer-1", "ASC_PRIVATE_KEY": KEY}
    return appstore.Credentials.from_env(env, tmp_path / "keys")


def client(tmp_path, answers=None, run=None, clock=lambda: 0.0, sleeps=None):
    apple = FakeApple(answers or {})
    sleep = sleeps.append if sleeps is not None else (lambda seconds: None)
    connect = appstore.AppStoreConnect(
        credentials(tmp_path), run=run or FakeRun(), send=apple, clock=clock, sleep=sleep
    )
    return connect, apple


def test_credentials_write_the_key_for_altool(tmp_path):
    creds = credentials(tmp_path)
    assert creds.key_path == tmp_path / "keys" / "AuthKey_KEY123.p8"
    assert creds.key_path.read_text(encoding="utf-8") == KEY
    assert stat.S_IMODE(creds.key_path.stat().st_mode) == 0o600


def test_credentials_name_a_missing_variable(tmp_path):
    with pytest.raises(SystemExit, match="ASC_ISSUER_ID"):
        appstore.Credentials.from_env({"ASC_KEY_ID": "K", "ASC_PRIVATE_KEY": KEY}, tmp_path)


def test_the_token_lasts_fifteen_minutes(tmp_path):
    now = [0.0]
    run = FakeRun()
    connect, _ = client(tmp_path, run=run, clock=lambda: now[0])
    assert connect.token() == TOKEN
    now[0] = 14 * 60
    connect.token()
    assert len(run.calls) == 1
    now[0] = 16 * 60
    connect.token()
    assert len(run.calls) == 2
    key_path = str(tmp_path / "keys" / "AuthKey_KEY123.p8")
    assert run.calls[0][0] == [
        "xcrun", "altool", "--generate-jwt", "--api-key", "KEY123",
        "--api-issuer", "issuer-1", "--p8-file-path", key_path,
    ]  # fmt: skip


def test_requests_retry_when_apple_is_busy(tmp_path):
    sleeps = []
    answers = {("GET", "/v1/apps/1"): [(429, {}), (503, {}), (200, {"data": {"id": "1"}})]}
    connect, apple = client(tmp_path, answers, sleeps=sleeps)
    assert connect.request("GET", "/v1/apps/1") == {"data": {"id": "1"}}
    assert sleeps == [2, 4]
    assert all(headers["Authorization"] == f"Bearer {TOKEN}" for _, _, headers, _ in apple.requests)


def test_errors_carry_apples_detail(tmp_path):
    detail = "An asset pack with this identifier already exists."
    answers = {("POST", "/v1/backgroundAssets"): [(409, {"errors": [{"detail": detail}]})]}
    connect, _ = client(tmp_path, answers)
    with pytest.raises(appstore.AppStoreError, match="409") as error:
        connect.request("POST", "/v1/backgroundAssets", {"data": {}})
    assert detail in str(error.value)


def test_finds_the_app_by_bundle_id(tmp_path):
    apps = [
        {"id": "2", "attributes": {"bundleId": "com.danciuclaudiu.gamba.beta"}},
        {"id": "1", "attributes": {"bundleId": "com.danciuclaudiu.gamba"}},
    ]
    answers = {
        ("GET", "/v1/apps?filter[bundleId]=com.danciuclaudiu.gamba"): [(200, {"data": apps})]
    }
    connect, _ = client(tmp_path, answers)
    assert connect.app_id() == "1"


def test_no_app_for_the_bundle_id(tmp_path):
    answers = {("GET", "/v1/apps?filter[bundleId]=com.danciuclaudiu.gamba"): [(200, {"data": []})]}
    connect, _ = client(tmp_path, answers)
    with pytest.raises(
        appstore.AppStoreError, match="no app with bundle ID com.danciuclaudiu.gamba"
    ):
        connect.app_id()


def test_creates_a_missing_asset_pack_record(tmp_path):
    answers = {
        ("GET", "/v1/apps/1/backgroundAssets?filter[assetPackIdentifier]=food-ro"): [
            (200, {"data": []})
        ],
        ("POST", "/v1/backgroundAssets"): [(201, {"data": {"id": "asset-ro"}})],
    }
    connect, apple = client(tmp_path, answers)
    assert connect.asset_id("1", "food-ro") == "asset-ro"
    assert apple.requests[1][3] == {
        "data": {
            "type": "backgroundAssets",
            "attributes": {"assetPackIdentifier": "food-ro"},
            "relationships": {"app": {"data": {"type": "apps", "id": "1"}}},
        }
    }


def test_reuses_an_asset_pack_record(tmp_path):
    answers = {
        ("GET", "/v1/apps/1/backgroundAssets?filter[assetPackIdentifier]=food-ro"): [
            (200, {"data": [{"id": "asset-ro"}]})
        ]
    }
    connect, apple = client(tmp_path, answers)
    assert connect.asset_id("1", "food-ro") == "asset-ro"
    assert [method for method, *_ in apple.requests] == ["GET"]


def test_reads_the_latest_version(tmp_path):
    version = {
        "id": "v3",
        "attributes": {
            "version": "3",
            "state": "FAILED",
            "stateDetails": {"errors": [{"code": "E1", "description": "Invalid manifest"}]},
        },
    }
    path = "/v1/backgroundAssets/asset-ro/versions?sort=-version&limit=1"
    connect, _ = client(
        tmp_path, {("GET", path): [(200, {"data": [version]}), (200, {"data": []})]}
    )
    assert connect.latest_version("asset-ro") == appstore.Version(
        id="v3", version="3", state="FAILED", errors=("Invalid manifest",)
    )
    assert connect.latest_version("asset-ro") is None


def test_uploads_with_altool(tmp_path):
    run = FakeRun(stdout="No errors uploading 'food-ro.aar'\n")
    connect, _ = client(tmp_path, run=run)
    connect.upload(tmp_path / "food-ro.aar", "1")
    args, kwargs = run.calls[0]
    assert args == [
        "xcrun", "altool", "--upload-asset-pack", str(tmp_path / "food-ro.aar"),
        "--apple-id", "1", "--api-key", "KEY123", "--api-issuer", "issuer-1",
    ]  # fmt: skip
    assert kwargs["env"]["API_PRIVATE_KEYS_DIR"] == str(tmp_path / "keys")


def test_a_failed_altool_upload_raises(tmp_path):
    connect, _ = client(tmp_path, run=FakeRun(stdout="ERROR: 400 invalid values\n", code=1))
    with pytest.raises(appstore.AppStoreError, match="400 invalid values"):
        connect.upload(tmp_path / "food-ro.aar", "1")


def test_finds_an_open_review_submission(tmp_path):
    path = (
        "/v1/reviewSubmissions?filter[app]=1&filter[platform]=IOS"
        "&filter[state]=READY_FOR_REVIEW,UNRESOLVED_ISSUES"
    )
    answers = {("GET", path): [(200, {"data": [{"id": "s1"}]}), (200, {"data": []})]}
    connect, _ = client(tmp_path, answers)
    assert connect.open_submission("1") == "s1"
    assert connect.open_submission("1") is None


def test_submits_versions_for_review(tmp_path):
    answers = {
        ("POST", "/v1/reviewSubmissions"): [(201, {"data": {"id": "s1"}})],
        ("POST", "/v1/reviewSubmissionItems"): [(201, {"data": {"id": "i1"}})] * 2,
        ("PATCH", "/v1/reviewSubmissions/s1"): [(200, {"data": {"id": "s1"}})],
    }
    connect, apple = client(tmp_path, answers)
    assert connect.submit("1", ["v3", "v7"]) == "s1"
    assert [(method, path) for method, path, *_ in apple.requests] == [
        ("POST", "/v1/reviewSubmissions"),
        ("POST", "/v1/reviewSubmissionItems"),
        ("POST", "/v1/reviewSubmissionItems"),
        ("PATCH", "/v1/reviewSubmissions/s1"),
    ]
    bodies = [body for *_, body in apple.requests]
    assert bodies[0] == {
        "data": {
            "type": "reviewSubmissions",
            "attributes": {"platform": "IOS"},
            "relationships": {"app": {"data": {"type": "apps", "id": "1"}}},
        }
    }
    assert bodies[2] == {
        "data": {
            "type": "reviewSubmissionItems",
            "relationships": {
                "reviewSubmission": {"data": {"type": "reviewSubmissions", "id": "s1"}},
                "backgroundAssetVersion": {"data": {"type": "backgroundAssetVersions", "id": "v7"}},
            },
        }
    }
    assert bodies[3] == {
        "data": {"type": "reviewSubmissions", "id": "s1", "attributes": {"submitted": True}}
    }
