import json
from pathlib import Path
from typer.testing import CliRunner
import pytest

from iwe.cli import app

runner = CliRunner()


@pytest.fixture
def sample_bundle_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    bundle_dir = tmp_path / "templates" / "test-doc"
    bundle_dir.mkdir(parents=True)
    
    # template.html
    template_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <style>
        body { font-family: sans-serif; margin: 20px; }
        h1 { color: #2c3e50; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <p>Value: {{ count }}</p>
    <div id="render-ready"></div>
</body>
</html>"""
    (bundle_dir / "template.html").write_text(template_html, encoding="utf-8")

    # schema.py
    schema_py = """from pydantic import BaseModel
class Schema(BaseModel):
    title: str
    count: int
"""
    (bundle_dir / "schema.py").write_text(schema_py, encoding="utf-8")

    # config.json
    config_json = {
        "format": "A4",
        "landscape": False,
        "print_background": True,
        "margin": {"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"}
    }
    (bundle_dir / "config.json").write_text(json.dumps(config_json), encoding="utf-8")

    # sample.json
    sample_json = {"title": "Invoice #101", "count": 42}
    (bundle_dir / "sample.json").write_text(json.dumps(sample_json), encoding="utf-8")

    return bundle_dir


def test_cli_generate_success(sample_bundle_dir: Path, tmp_path: Path):
    sample_json_path = sample_bundle_dir / "sample.json"
    result = runner.invoke(app, ["generate", "test-doc", "--data", str(sample_json_path)])
    
    assert result.exit_code == 0, result.stderr
    assert "Generated PDF:" in result.stdout
    
    # Verify generated PDF in default generated/ directory
    generated_dir = tmp_path / "generated"
    assert generated_dir.exists()
    pdf_files = list(generated_dir.glob("*.pdf"))
    assert len(pdf_files) == 1
    
    # Check PDF magic bytes
    pdf_bytes = pdf_files[0].read_bytes()
    assert pdf_bytes.startswith(b"%PDF-")


def test_cli_generate_custom_output(sample_bundle_dir: Path, tmp_path: Path):
    custom_pdf = tmp_path / "custom_output" / "my_doc.pdf"
    result = runner.invoke(app, [
        "generate", "test-doc",
        "--data", '{"title": "Custom Test", "count": 7}',
        "--output", str(custom_pdf),
    ])
    
    assert result.exit_code == 0, result.stderr
    assert custom_pdf.exists()
    assert custom_pdf.read_bytes().startswith(b"%PDF-")


def test_cli_generate_validation_failure(sample_bundle_dir: Path):
    # Missing required 'count' field
    result = runner.invoke(app, ["generate", "test-doc", "--data", '{"title": "No Count"}'])
    assert result.exit_code == 1
    assert "Validation error" in result.stderr or "validation error" in result.stdout or "Validation error" in result.stdout


def test_cli_generate_bundle_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "templates").mkdir()
    result = runner.invoke(app, ["generate", "does-not-exist", "--data", '{"a": 1}'])
    assert result.exit_code == 1
