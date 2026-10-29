import json
from pathlib import Path
from typer.testing import CliRunner
import pytest

from iwe.cli import app

runner = CliRunner()


def test_cli_list_empty_templates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "templates").mkdir()
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No template bundles found" in result.stdout or "Available Template Bundles" in result.stdout


def test_cli_list_with_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    bundle_dir = tmp_path / "templates" / "test-bundle"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "template.html").write_text("<h1>{{ title }}</h1>", encoding="utf-8")
    (bundle_dir / "schema.py").write_text(
        "from pydantic import BaseModel\nclass Schema(BaseModel):\n    title: str\n",
        encoding="utf-8",
    )
    (bundle_dir / "config.json").write_text(json.dumps({"format": "A4"}), encoding="utf-8")
    (bundle_dir / "sample.json").write_text(json.dumps({"title": "Sample Title"}), encoding="utf-8")

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "test-bundle" in result.stdout


def test_cli_sample_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    bundle_dir = tmp_path / "templates" / "test-bundle"
    bundle_dir.mkdir(parents=True)
    sample_payload = {"title": "Hello iwe"}
    (bundle_dir / "sample.json").write_text(json.dumps(sample_payload), encoding="utf-8")

    result = runner.invoke(app, ["sample", "test-bundle"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["title"] == "Hello iwe"


def test_cli_sample_bundle_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "templates").mkdir()
    result = runner.invoke(app, ["sample", "non-existent"])
    assert result.exit_code == 1
    assert "Template bundle 'non-existent' not found" in result.stderr or "Template bundle 'non-existent' not found" in result.stdout
