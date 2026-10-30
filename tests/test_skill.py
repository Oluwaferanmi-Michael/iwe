import json
from pathlib import Path
from typer.testing import CliRunner

from iwe.cli import app
from iwe.skill import install_skill


runner = CliRunner()


def test_install_skill_file(tmp_path: Path):
    target_skill = tmp_path / ".agents" / "skills" / "iwe" / "SKILL.md"
    written_path = install_skill(target_file=target_skill)

    assert written_path.is_file()
    content = written_path.read_text(encoding="utf-8")
    assert "name: iwe" in content
    assert "Template Bundle" in content
    assert "iwe new" in content


def test_cli_skill_install(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["skill", "install"])
    assert result.exit_code == 0
    assert "Successfully installed agent skill" in result.stdout
    assert (tmp_path / ".agents" / "skills" / "iwe" / "SKILL.md").is_file()


def test_cli_skill_install_json(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["skill", "install", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["status"] == "success"
    assert ".agents" in data["installed_path"]
