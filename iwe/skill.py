"""Agent skill installation module for iwe."""

from pathlib import Path


def _get_skill_source_path() -> Path:
    """Return the filesystem path to the packaged SKILL.md file."""
    return Path(__file__).resolve().parent / "resources" / "skills" / "iwe" / "SKILL.md"


def install_skill(target_file: Path | None = None) -> Path:
    """Install the iwe agent skill into .agents/skills/iwe/SKILL.md.

    Args:
        target_file: Optional custom destination file path. Defaults to
            `./.agents/skills/iwe/SKILL.md` in the current working directory.

    Returns:
        Path: Path to the written SKILL.md file.

    Raises:
        FileNotFoundError: If the packaged SKILL.md source cannot be found.
    """
    source_file = _get_skill_source_path()
    if not source_file.is_file():
        raise FileNotFoundError(f"Packaged skill source not found at {source_file}")

    dest = target_file or (Path.cwd() / ".agents" / "skills" / "iwe" / "SKILL.md")
    dest.parent.mkdir(parents=True, exist_ok=True)

    content = source_file.read_text(encoding="utf-8")
    dest.write_text(content, encoding="utf-8")

    return dest
