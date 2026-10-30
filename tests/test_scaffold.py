import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from iwe.cli import app
from iwe.bundle import BundleManager
from iwe.scaffold import scaffold_bundle, validate_bundle_name


runner = CliRunner()


def test_validate_bundle_name():
    validate_bundle_name("valid-name")
    validate_bundle_name("valid_name_123")
    with pytest.raises(ValueError):
        validate_bundle_name("invalid name with spaces")
    with pytest.raises(ValueError):
        validate_bundle_name("invalid/slash")
    with pytest.raises(ValueError):
        validate_bundle_name("")


def test_scaffold_bundle_creates_runnable_bundle(tmp_path: Path):
    templates_dir = tmp_path / "iwe-templates"
    bundle_dir = scaffold_bundle("test-bundle", templates_dir=templates_dir)

    assert bundle_dir.is_dir()
    assert (bundle_dir / "template.html").is_file()
    assert (bundle_dir / "schema.py").is_file()
    assert (bundle_dir / "config.json").is_file()
    assert (bundle_dir / "sample.json").is_file()
    assert (bundle_dir / "assets").is_dir()

    # Verify bundle manager discovery and loading
    manager = BundleManager(templates_dir=templates_dir)
    bundle = manager.get_bundle("test-bundle")
    assert bundle.has_template
    assert bundle.has_schema
    assert bundle.has_config
    assert bundle.has_sample

    # Test dynamic schema loading
    schema_cls = bundle.get_schema_class()
    sample_data = bundle.get_sample_data()
    validated = schema_cls(**sample_data)
    assert validated.title == "Test Bundle"


def test_scaffold_duplicate_error(tmp_path: Path):
    templates_dir = tmp_path / "iwe-templates"
    scaffold_bundle("dup-bundle", templates_dir=templates_dir)
    with pytest.raises(FileExistsError):
        scaffold_bundle("dup-bundle", templates_dir=templates_dir)


def test_cli_new_bundle(tmp_path: Path):
    templates_dir = tmp_path / "iwe-templates"
    result = runner.invoke(app, ["new", "cli-bundle", "-t", str(templates_dir)])
    assert result.exit_code == 0
    assert "Successfully created template bundle" in result.stdout
    assert (templates_dir / "cli-bundle" / "template.html").exists()


def test_cli_new_bundle_json_mode(tmp_path: Path):
    templates_dir = tmp_path / "iwe-templates"
    result = runner.invoke(app, ["new", "json-bundle", "-t", str(templates_dir), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["status"] == "success"
    assert data["bundle_name"] == "json-bundle"
