import re
from pathlib import Path

import pytest

from gamba_pipeline import cli

WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
WORKFLOW = WORKFLOWS / "packs.yml"


def test_the_workflow_runs_the_full_build_in_order():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert re.findall(r"uv run gamba-pipeline ([\w-]+)", text) == [
        "pin-latest", "download", "reference", "packs", "package", "survey",
        "spotcheck", "release", "report", "upload", "upload", "review",
    ]  # fmt: skip
    assert "pull_request" not in text and "continue-on-error" not in text
    assert "runs-on: xcode-27" in text
    assert "--submit" not in text


def test_the_daily_review_runs_only_review():
    text = (WORKFLOWS / "review.yml").read_text(encoding="utf-8")
    assert re.findall(r"uv run gamba-pipeline ([\w-]+)", text) == ["review"]
    assert "pull_request" not in text and "continue-on-error" not in text
    assert "vars.PACK_DELIVERY == 'app-store'" in text
    assert "runs-on: xcode-27" in text


@pytest.mark.parametrize("command", ["pin-latest", "upload", "release", "review"])
def test_the_workflows_new_commands_exist(command):
    with pytest.raises(SystemExit) as exit:
        cli.main([command, "--help"])
    assert exit.value.code == 0
