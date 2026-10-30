"""Template bundle scaffolding module for iwe."""

import json
from pathlib import Path
import re
import typer

from iwe.bundle import resolve_templates_dir


def _get_boilerplate_dir() -> Path:
    """Return the filesystem path to the packaged boilerplate directory."""
    return Path(__file__).resolve().parent / "resources" / "boilerplate"


def validate_bundle_name(name: str) -> None:
    """Ensure bundle name is a valid URL- and filesystem-safe slug.

    Args:
        name: Proposed directory name for the bundle.

    Raises:
        ValueError: If name is empty, contains spaces, or invalid characters.
    """
    if not name or not re.match(r"^[a-zA-Z0-9_\-]+$", name):
        raise ValueError(
            f"Invalid bundle name '{name}'. Bundle names must contain only letters, numbers, hyphens, and underscores."
        )


def scaffold_bundle(
    bundle_name: str,
    templates_dir: Path | None = None,
    interactive: bool = False,
    title: str | None = None,
    paper_format: str = "A4",
    landscape: bool = False,
) -> Path:
    """Scaffold a new runnable minimal Template Bundle in the templates directory.

    Args:
        bundle_name: Unique slug name for the new template bundle directory.
        templates_dir: Optional custom destination root. Defaults via 4-tier resolution.
        interactive: If True, prompt user for initial document title and print layout.
        title: Optional document title override.
        paper_format: Paper size (e.g. A4, Letter).
        landscape: Orientation flag.

    Returns:
        Path: Path to the newly created bundle directory.

    Raises:
        ValueError: If bundle_name is invalid.
        FileExistsError: If target directory already exists.
    """
    validate_bundle_name(bundle_name)

    target_root = resolve_templates_dir(templates_dir, prefer_creation=True)
    target_root.mkdir(parents=True, exist_ok=True)

    bundle_dir = target_root / bundle_name
    if bundle_dir.exists():
        raise FileExistsError(f"Template bundle '{bundle_name}' already exists at {bundle_dir}")

    doc_title = title or bundle_name.replace("-", " ").replace("_", " ").title()
    doc_format = paper_format
    doc_landscape = landscape

    if interactive:
        doc_title = typer.prompt("Document title", default=doc_title)
        doc_format = typer.prompt("Paper format (A4, Letter, Legal)", default=doc_format).strip().upper()
        doc_landscape = typer.confirm("Landscape orientation?", default=doc_landscape)

    # Create bundle directory and assets subfolder
    bundle_dir.mkdir(parents=True, exist_ok=False)
    assets_dir = bundle_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    boilerplate_dir = _get_boilerplate_dir()

    # 1. template.html
    template_content = (boilerplate_dir / "template.html").read_text(encoding="utf-8")
    (bundle_dir / "template.html").write_text(template_content, encoding="utf-8")

    # 2. schema.py
    schema_content = (boilerplate_dir / "schema.py").read_text(encoding="utf-8")
    (bundle_dir / "schema.py").write_text(schema_content, encoding="utf-8")

    # 3. config.json
    config_data = {
        "format": doc_format,
        "margin": "10mm",
        "landscape": doc_landscape,
    }
    (bundle_dir / "config.json").write_text(json.dumps(config_data, indent=2) + "\n", encoding="utf-8")

    # 4. sample.json
    sample_data = {
        "title": doc_title,
        "content": f"This is a starter document bundle for '{doc_title}' rendered with iwe.",
    }
    (bundle_dir / "sample.json").write_text(json.dumps(sample_data, indent=2) + "\n", encoding="utf-8")

    return bundle_dir
