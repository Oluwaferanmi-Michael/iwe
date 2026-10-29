from datetime import datetime
import json
from pathlib import Path
from typing import Optional
import webbrowser
import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from iwe.bundle import BundleManager, BundleNotFoundError, SchemaLoadError
from iwe.compiler import TemplateCompiler, load_payload_data, validate_payload
from iwe.renderer import PdfRenderer, PdfRenderError

app = typer.Typer(
    name="iwe",
    help="iwe - CLI tool and engine for generating PDF documents from external HTML/Jinja2 template bundles.",
    no_args_is_help=True,
)

console = Console()
err_console = Console(stderr=True)


@app.command("list")
def list_bundles(
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        "-t",
        help="Path to the directory containing template bundles.",
    ),
) -> None:
    """List all available template bundles."""
    manager = BundleManager(templates_dir=templates_dir)
    bundles = manager.list_bundles()

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
            "✓" if bundle.has_template else "✗",
            "✓" if bundle.has_schema else "✗",
            "✓" if bundle.has_config else "✗",
            "✓" if bundle.has_sample else "✗",
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
    """Print the sample payload for a given template bundle."""
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
) -> None:
    """Compile and preview a template bundle in a web browser without emitting a PDF."""
    manager = BundleManager(templates_dir=templates_dir)

    try:
        bundle = manager.get_bundle(bundle_name)
    except BundleNotFoundError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    try:
        raw_data = load_payload_data(data)
    except Exception as e:
        err_console.print(f"[red]Payload Error:[/red] {e}")
        raise typer.Exit(code=1)

    try:
        schema_cls = bundle.get_schema_class()
        validated_payload = validate_payload(raw_data, schema_cls)
    except SchemaLoadError as e:
        err_console.print(f"[red]Schema Error:[/red] {e}")
        raise typer.Exit(code=1)
    except ValidationError as e:
        err_console.print(f"[red]Validation error for bundle '{bundle_name}':[/red]")
        for err in e.errors():
            loc = " -> ".join(str(loc_item) for loc_item in err["loc"])
            err_console.print(f"  • [yellow]{loc}[/yellow]: {err['msg']}")
        raise typer.Exit(code=1)

    try:
        compiler = TemplateCompiler(bundle)
        rendered_html = compiler.compile(validated_payload)
    except Exception as e:
        err_console.print(f"[red]Compilation Error:[/red] {e}")
        raise typer.Exit(code=1)

    preview_file = bundle.path / "_preview.html"
    preview_file.write_text(rendered_html, encoding="utf-8")
    preview_uri = preview_file.resolve().as_uri()

    console.print(f"[green]✓ Opening preview in browser:[/green] {preview_uri}")
    if open_browser:
        webbrowser.open(preview_uri)


@app.command("generate")
def generate(
    bundle_name: str = typer.Argument(..., help="Name of the template bundle to generate from."),
    data: str = typer.Option(..., "--data", "-d", help="Path to JSON payload file or raw inline JSON string."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Custom destination path for the output PDF."),
    format: Optional[str] = typer.Option(None, "--format", "-f", help="Page format (e.g. A4, Letter)."),
    landscape: Optional[bool] = typer.Option(None, "--landscape", help="Render in landscape orientation."),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        "-t",
        help="Path to the directory containing template bundles.",
    ),
) -> None:
    """Generate a PDF document from a template bundle and payload."""
    manager = BundleManager(templates_dir=templates_dir)

    # 1. Locate bundle
    try:
        bundle = manager.get_bundle(bundle_name)
    except BundleNotFoundError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    # 2. Load payload data
    try:
        raw_data = load_payload_data(data)
    except Exception as e:
        err_console.print(f"[red]Payload Error:[/red] {e}")
        raise typer.Exit(code=1)

    # 3. Validate against bundle schema
    try:
        schema_cls = bundle.get_schema_class()
        validated_payload = validate_payload(raw_data, schema_cls)
    except SchemaLoadError as e:
        err_console.print(f"[red]Schema Error:[/red] {e}")
        raise typer.Exit(code=1)
    except ValidationError as e:
        err_console.print(f"[red]Validation error for bundle '{bundle_name}':[/red]")
        for err in e.errors():
            loc = " -> ".join(str(loc_item) for loc_item in err["loc"])
            err_console.print(f"  • [yellow]{loc}[/yellow]: {err['msg']}")
        raise typer.Exit(code=1)

    # 4. Compile HTML template
    try:
        compiler = TemplateCompiler(bundle)
        rendered_html = compiler.compile(validated_payload)
    except Exception as e:
        err_console.print(f"[red]Compilation Error:[/red] {e}")
        raise typer.Exit(code=1)

    # 5. Determine output destination
    if output is not None:
        target_output = output
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target_output = Path.cwd() / "generated" / f"{bundle_name}-{timestamp}.pdf"

    # 6. Prepare config and CLI overrides
    config = bundle.get_config()
    if format:
        config["format"] = format
    if landscape is not None:
        config["landscape"] = landscape

    # 7. Render PDF via Playwright
    renderer = PdfRenderer()
    try:
        final_pdf_path = renderer.render(
            html_content=rendered_html,
            output_path=target_output,
            base_dir=bundle.path,
            config=config,
        )
        console.print(f"[green]✓ Generated PDF:[/green] {final_pdf_path}")
    except PdfRenderError as e:
        err_console.print(f"[red]Rendering Error:[/red] {e}")
        raise typer.Exit(code=2)


if __name__ == "__main__":
    app()
