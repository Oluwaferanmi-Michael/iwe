"""Command-line interface and execution runner for iwe.

This module provides the Typer CLI application for discovering template bundles,
inspecting sample mock payloads, previewing compiled templates in web browsers,
and generating PDF documents with configurable paper sizes and margins.
"""

from datetime import datetime
import json
from pathlib import Path
import tempfile
from typing import Any, Optional, Tuple
import webbrowser
import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from iwe.bundle import BundleManager, BundleNotFoundError, SchemaLoadError, TemplateBundle
from iwe.compiler import TemplateCompiler, load_payload_data, validate_payload
from iwe.renderer import PdfRenderer, PdfRenderError

app = typer.Typer(
    name="iwe",
    help="iwe - CLI tool and engine for generating PDF documents from external HTML/Jinja2 template bundles.",
    no_args_is_help=True,
)

console = Console()
err_console = Console(stderr=True)


def _prepare_rendered_document(
    bundle_name: str,
    data: str,
    templates_dir: Optional[Path] = None,
    json_mode: bool = False,
) -> Tuple[TemplateBundle, str]:
    """Helper to locate a bundle, validate its payload, and compile its HTML template.

    Args:
        bundle_name: Slug name of the target template bundle.
        data: Path to JSON payload file or inline JSON string.
        templates_dir: Optional custom path to templates root directory.
        json_mode: If True, error messages are formatted as JSON on stderr.

    Returns:
        Tuple[TemplateBundle, str]: A tuple of the resolved TemplateBundle object
            and the fully compiled HTML string.

    Raises:
        typer.Exit(code=1): If bundle is missing, payload is invalid JSON, schema
            loading fails, or payload validation fails.
    """
    manager = BundleManager(templates_dir=templates_dir)

    # 1. Locate bundle
    try:
        bundle = manager.get_bundle(bundle_name)
    except BundleNotFoundError as e:
        if json_mode:
            err_console.print_json(json.dumps({"status": "error", "type": "BundleNotFoundError", "message": str(e)}))
        else:
            err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    # 2. Load payload data
    try:
        raw_data = load_payload_data(data)
    except Exception as e:
        if json_mode:
            err_console.print_json(json.dumps({"status": "error", "type": "PayloadError", "message": str(e)}))
        else:
            err_console.print(f"[red]Payload Error:[/red] {e}")
        raise typer.Exit(code=1)

    # 3. Validate against bundle schema
    try:
        schema_cls = bundle.get_schema_class()
        validated_payload = validate_payload(raw_data, schema_cls)
    except SchemaLoadError as e:
        if json_mode:
            err_console.print_json(json.dumps({"status": "error", "type": "SchemaLoadError", "message": str(e)}))
        else:
            err_console.print(f"[red]Schema Error:[/red] {e}")
        raise typer.Exit(code=1)
    except ValidationError as e:
        errors = [
            {"loc": " -> ".join(str(loc_item) for loc_item in err["loc"]), "msg": err["msg"]}
            for err in e.errors()
        ]
        if json_mode:
            err_console.print_json(json.dumps({"status": "error", "type": "ValidationError", "errors": errors}))
        else:
            err_console.print(f"[red]Validation error for bundle '{bundle_name}':[/red]")
            for item in errors:
                err_console.print(f"  * [yellow]{item['loc']}[/yellow]: {item['msg']}")
        raise typer.Exit(code=1)

    # 4. Compile HTML template
    try:
        compiler = TemplateCompiler(bundle)
        rendered_html = compiler.compile(validated_payload)
    except Exception as e:
        if json_mode:
            err_console.print_json(json.dumps({"status": "error", "type": "CompilationError", "message": str(e)}))
        else:
            err_console.print(f"[red]Compilation Error:[/red] {e}")
        raise typer.Exit(code=1)

    return bundle, rendered_html


@app.command("list")
def list_bundles(
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        "-t",
        help="Path to the directory containing template bundles.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format."),
) -> None:
    """List all available template bundles on disk."""
    manager = BundleManager(templates_dir=templates_dir)
    bundles = manager.list_bundles()

    if json_output:
        bundle_list = [
            {
                "name": b.name,
                "has_template": b.has_template,
                "has_schema": b.has_schema,
                "has_config": b.has_config,
                "has_sample": b.has_sample,
            }
            for b in bundles
        ]
        console.print_json(json.dumps(bundle_list))
        return

    if not bundles:
        console.print("[yellow]No template bundles found.[/yellow]")
        return

    table = Table(title="Available Template Bundles")
    table.add_column("Bundle Name", style="cyan", no_wrap=True)
    table.add_column("Template", style="green")
    table.add_column("Schema", style="magenta")
    table.add_column("Config", style="blue")
    table.add_column("Sample Data", style="yellow")

    for bundle in bundles:
        table.add_row(
            bundle.name,
            "[green]yes[/green]" if bundle.has_template else "[dim]no[/dim]",
            "[green]yes[/green]" if bundle.has_schema else "[dim]no[/dim]",
            "[green]yes[/green]" if bundle.has_config else "[dim]no[/dim]",
            "[green]yes[/green]" if bundle.has_sample else "[dim]no[/dim]",
        )

    console.print(table)


@app.command("sample")
def show_sample(
    bundle_name: str = typer.Argument(..., help="Name of the template bundle to inspect."),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        "-t",
        help="Path to the directory containing template bundles.",
    ),
) -> None:
    """Print the sample payload for a given template bundle formatted as JSON."""
    manager = BundleManager(templates_dir=templates_dir)
    try:
        bundle = manager.get_bundle(bundle_name)
        data = bundle.get_sample_data()
        console.print_json(json.dumps(data))
    except (BundleNotFoundError, FileNotFoundError) as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        err_console.print(f"[red]Error loading sample:[/red] {e}")
        raise typer.Exit(code=1)


@app.command("preview")
def preview(
    bundle_name: str = typer.Argument(..., help="Name of the template bundle to preview."),
    data: str = typer.Option(..., "--data", "-d", help="Path to JSON payload file or raw inline JSON string."),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Whether to automatically open browser."),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        "-t",
        help="Path to the directory containing template bundles.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format."),
) -> None:
    """Compile and preview a template bundle in a web browser without emitting a PDF."""
    bundle, rendered_html = _prepare_rendered_document(bundle_name, data, templates_dir, json_mode=json_output)

    # Write preview HTML into system temp directory to prevent bundle pollution
    temp_dir = Path(tempfile.gettempdir()) / "iwe_previews"
    temp_dir.mkdir(parents=True, exist_ok=True)
    preview_file = temp_dir / f"{bundle_name}_preview.html"

    # Inject base href pointing to bundle path so relative images/fonts load correctly
    base_uri = bundle.path.resolve().as_uri() + "/"
    base_tag = f'<base href="{base_uri}">'
    if "<head>" in rendered_html:
        prepared_preview_html = rendered_html.replace("<head>", f"<head>\n    {base_tag}", 1)
    else:
        prepared_preview_html = f"<head>{base_tag}</head>\n" + rendered_html

    preview_file.write_text(prepared_preview_html, encoding="utf-8")
    preview_uri = preview_file.resolve().as_uri()

    if json_output:
        console.print_json(json.dumps({"status": "success", "preview_uri": preview_uri, "file": str(preview_file)}))
    else:
        console.print(f"[green]Opening preview in browser:[/green] {preview_uri}")

    if open_browser:
        webbrowser.open(preview_uri)


@app.command("generate")
def generate(
    bundle_name: str = typer.Argument(..., help="Name of the template bundle to generate from."),
    data: str = typer.Option(..., "--data", "-d", help="Path to JSON payload file or raw inline JSON string."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Custom destination path for the output PDF."),
    format: Optional[str] = typer.Option(None, "--format", "-f", help="Page format (e.g. A4, Letter)."),
    landscape: Optional[bool] = typer.Option(None, "--landscape", help="Render in landscape orientation."),
    margin: Optional[str] = typer.Option(None, "--margin", "-m", help="Override margins (e.g. '10mm' or 'top=10mm,bottom=10mm,left=15mm,right=15mm')."),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        "-t",
        help="Path to the directory containing template bundles.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format."),
) -> None:
    """Generate a publication-grade PDF document from a template bundle and payload."""
    bundle, rendered_html = _prepare_rendered_document(bundle_name, data, templates_dir, json_mode=json_output)

    # Determine output destination
    if output is not None:
        target_output = output
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target_output = Path.cwd() / "generated" / f"{bundle_name}-{timestamp}.pdf"

    # Prepare config and CLI overrides
    config = bundle.get_config()
    if format:
        config["format"] = format
    if landscape is not None:
        config["landscape"] = landscape
    if margin:
        if "=" in margin:
            margin_dict = {}
            for part in margin.split(","):
                k, v = part.split("=", 1)
                margin_dict[k.strip()] = v.strip()
            config["margin"] = margin_dict
        else:
            config["margin"] = {
                "top": margin.strip(),
                "bottom": margin.strip(),
                "left": margin.strip(),
                "right": margin.strip(),
            }

    # Render PDF via Playwright
    renderer = PdfRenderer()
    try:
        final_pdf_path = renderer.render(
            html_content=rendered_html,
            output_path=target_output,
            base_dir=bundle.path,
            config=config,
        )
        if json_output:
            console.print_json(json.dumps({
                "status": "success",
                "document_path": str(final_pdf_path),
                "bundle": bundle_name,
            }))
        else:
            console.print(f"[green]Generated Document:[/green] {final_pdf_path}")
    except PdfRenderError as e:
        if json_output:
            err_console.print_json(json.dumps({"status": "error", "type": "PdfRenderError", "message": str(e)}))
        else:
            err_console.print(f"[red]Rendering Error:[/red] {e}")
        raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
