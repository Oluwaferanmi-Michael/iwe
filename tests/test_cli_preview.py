import json
from pathlib import Path
from typer.testing import CliRunner
import pytest

from iwe.cli import app

runner = CliRunner()


@pytest.fixture
def sample_bundle_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    bundle_dir = tmp_path / "templates" / "preview-doc"
    bundle_dir.mkdir(parents=True)
    
    (bundle_dir / "template.html").write_text("<h1>{{ title }}</h1><p>{{ value }}</p>", encoding="utf-8")
    (bundle_dir / "schema.py").write_text("from pydantic import BaseModel\nclass Schema(BaseModel):\n    title: str\n    value: int\n", encoding="utf-8")
    (bundle_dir / "config.json").write_text(json.dumps({"format": "A4"}), encoding="utf-8")
    (bundle_dir / "sample.json").write_text(json.dumps({"title": "Sample", "value": 100}), encoding="utf-8")

    return bundle_dir


def test_cli_preview_success(sample_bundle_dir: Path, monkeypatch: pytest.MonkeyPatch):
    opened_urls = []
    monkeypatch.setattr("webbrowser.open", lambda url: opened_urls.append(url))

    sample_json = sample_bundle_dir / "sample.json"
    result = runner.invoke(app, ["preview", "preview-doc", "--data", str(sample_json)])

    assert result.exit_code == 0
    assert "Opening preview in browser:" in result.stdout
    assert len(opened_urls) == 1
    assert "preview" in opened_urls[0]


def test_cli_preview_validation_failure(sample_bundle_dir: Path):
    result = runner.invoke(app, ["preview", "preview-doc", "--data", '{"title": "Missing Value"}'])
    assert result.exit_code == 1
    assert "Validation error" in result.stderr or "Validation error" in result.stdout


def test_cli_preview_bundle_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "templates").mkdir()
    result = runner.invoke(app, ["preview", "non-existent", "--data", '{"a": 1}'])
    assert result.exit_code == 1
