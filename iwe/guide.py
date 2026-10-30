"""Guide and documentation viewer module for iwe."""

from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown


def _get_docs_dir() -> Path:
    """Return the filesystem path to the packaged documentation directory."""
    return Path(__file__).resolve().parent / "resources" / "docs"


def get_guide_content(topic: str = "all") -> str:
    """Load documentation markdown content by topic.

    Args:
        topic: One of 'cli', 'templates', or 'all'.

    Returns:
        str: Combined or selected markdown text.
    """
    docs_dir = _get_docs_dir()
    cli_doc = (docs_dir / "CLI_GUIDE.md").read_text(encoding="utf-8") if (docs_dir / "CLI_GUIDE.md").is_file() else ""
    template_doc = (docs_dir / "TEMPLATE_GUIDE.md").read_text(encoding="utf-8") if (docs_dir / "TEMPLATE_GUIDE.md").is_file() else ""

    topic_clean = topic.strip().lower()
    if topic_clean == "cli":
        return cli_doc
    elif topic_clean in ("template", "templates"):
        return template_doc
    else:
        return f"{cli_doc}\n\n---\n\n{template_doc}"


def export_guides(destination_dir: Path) -> list[Path]:
    """Export markdown guides to a target directory.

    Args:
        destination_dir: Destination folder path.

    Returns:
        list[Path]: Paths of exported documentation files.
    """
    destination_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = _get_docs_dir()
    exported = []

    for doc_name in ["CLI_GUIDE.md", "TEMPLATE_GUIDE.md"]:
        src = docs_dir / doc_name
        if src.is_file():
            dst = destination_dir / doc_name
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            exported.append(dst)

    return exported


def display_guide(topic: str = "all", export_dir: Path | None = None, console: Console | None = None) -> None:
    """Display documentation in the terminal or export to markdown files.

    Args:
        topic: Selected topic ('cli', 'templates', 'all').
        export_dir: If provided, exports guide files to this directory.
        console: Optional Rich console instance.
    """
    cons = console or Console()

    if export_dir is not None:
        exported = export_guides(export_dir)
        cons.print(f"[green]Successfully exported {len(exported)} documentation file(s) to:[/green] {export_dir.resolve()}")
        for p in exported:
            cons.print(f"  * {p.name}")
        return

    content = get_guide_content(topic)
    md = Markdown(content)
    cons.print(md)
