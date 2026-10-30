from pathlib import Path
from typer.testing import CliRunner

from iwe.cli import app
from iwe.guide import get_guide_content, export_guides


runner = CliRunner()


def test_get_guide_content():
    cli_content = get_guide_content("cli")
    assert "iwe CLI Guide" in cli_content

    template_content = get_guide_content("templates")
    assert "iwe Template" in template_content

    all_content = get_guide_content("all")
    assert "iwe CLI Guide" in all_content
    assert "iwe Template" in all_content


def test_export_guides(tmp_path: Path):
    dest = tmp_path / "exported_docs"
    exported = export_guides(dest)
    assert len(exported) == 2
    assert (dest / "CLI_GUIDE.md").is_file()
    assert (dest / "TEMPLATE_GUIDE.md").is_file()


def test_cli_guide_display():
    result = runner.invoke(app, ["guide", "--topic", "cli"])
    assert result.exit_code == 0
    assert "iwe CLI Guide" in result.stdout


def test_cli_guide_export(tmp_path: Path):
    dest = tmp_path / "docs_out"
    result = runner.invoke(app, ["guide", "--export", str(dest)])
    assert result.exit_code == 0
    assert "Successfully exported" in result.stdout
    assert (dest / "CLI_GUIDE.md").is_file()
    assert (dest / "TEMPLATE_GUIDE.md").is_file()
