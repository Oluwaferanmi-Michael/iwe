from pathlib import Path
from typer.testing import CliRunner
import pytest

from iwe.cli import app
from iwe.renderer import normalize_paper_format, SUPPORTED_PAPER_FORMATS

runner = CliRunner()


def test_normalize_paper_format_cases():
    assert normalize_paper_format("a4") == "A4"
    assert normalize_paper_format("A4") == "A4"
    assert normalize_paper_format("letter") == "Letter"
    assert normalize_paper_format("Letter") == "Letter"
    assert normalize_paper_format("LEGAL") == "Legal"
    assert normalize_paper_format("tabloid") == "Tabloid"
    assert normalize_paper_format("a3") == "A3"
    assert normalize_paper_format("a5") == "A5"


def test_normalize_paper_format_invalid():
    with pytest.raises(ValueError, match="Unsupported paper format 'bogus'"):
        normalize_paper_format("bogus")


def test_cli_generate_with_lowercase_format(tmp_path: Path):
    sample_file = Path("templates/multi-page-report/sample.json")
    output_pdf = tmp_path / "format_test.pdf"

    result = runner.invoke(app, [
        "generate", "multi-page-report",
        "--data", str(sample_file),
        "--output", str(output_pdf),
        "--format", "a4",
    ])

    assert result.exit_code == 0, result.stderr
    assert output_pdf.exists()


def test_cli_generate_with_invalid_format(tmp_path: Path):
    sample_file = Path("templates/multi-page-report/sample.json")
    output_pdf = tmp_path / "fail.pdf"

    result = runner.invoke(app, [
        "generate", "multi-page-report",
        "--data", str(sample_file),
        "--output", str(output_pdf),
        "--format", "bogus_format",
    ])

    assert result.exit_code == 1
    assert "Unsupported paper format 'bogus_format'" in (result.stderr + result.stdout)
    assert "Supported formats are:" in (result.stderr + result.stdout)
