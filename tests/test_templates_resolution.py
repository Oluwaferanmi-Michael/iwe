from pathlib import Path
from iwe.bundle import resolve_templates_dir


def test_resolve_explicit_path(tmp_path: Path):
    custom = tmp_path / "custom"
    resolved = resolve_templates_dir(custom_path=custom)
    assert resolved == custom


def test_resolve_env_variable(tmp_path: Path, monkeypatch):
    env_dir = tmp_path / "from_env"
    monkeypatch.setenv("IWE_TEMPLATES_DIR", str(env_dir))
    resolved = resolve_templates_dir()
    assert resolved == env_dir


def test_resolve_local_iwe_templates(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("IWE_TEMPLATES_DIR", raising=False)
    local_iwe = tmp_path / "iwe-templates"
    local_iwe.mkdir()
    resolved = resolve_templates_dir()
    assert resolved == local_iwe


def test_resolve_legacy_templates(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("IWE_TEMPLATES_DIR", raising=False)
    legacy = tmp_path / "templates"
    legacy.mkdir()
    resolved = resolve_templates_dir()
    assert resolved == legacy


def test_resolve_prefer_creation(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("IWE_TEMPLATES_DIR", raising=False)
    resolved = resolve_templates_dir(prefer_creation=True)
    assert resolved == tmp_path / "iwe-templates"
