from pathlib import Path
from typer.testing import CliRunner
import pytest

from iwe.bundle import BundleManager
from iwe.cli import app

runner = CliRunner()


def test_reference_bundle_structure():
    manager = BundleManager()
    bundle = manager.get_bundle("multi-page-report")
    assert bundle.has_template
    assert bundle.has_schema
    assert bundle.has_config
    assert bundle.has_sample

    # Check schema validation with sample data
    schema_cls = bundle.get_schema_class()
    sample_data = bundle.get_sample_data()
    validated = schema_cls.model_validate(sample_data)
    assert validated.report_title


def test_reference_bundle_cli_generate(tmp_path: Path):
    manager = BundleManager()
    bundle = manager.get_bundle("multi-page-report")
    sample_file = bundle.sample_path
    output_pdf = tmp_path / "report_out.pdf"

    result = runner.invoke(app, [
        "generate", "multi-page-report",
        "--data", str(sample_file),
        "--output", str(output_pdf),
    ])

    assert result.exit_code == 0, result.stderr
    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 1000  # Multi-page PDF should have substantial size
    assert output_pdf.read_bytes().startswith(b"%PDF-")
