import json
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

from iwe.bundle import BundleManager, BundleNotFoundError

app = typer.Typer(
    name="iwe",
    help="iwe - CLI tool and engine for generating PDF documents from external HTML/Jinja2 template bundles.",
    no_args_is_help=True,
)

console = Console()
err_console = Console(stderr=True)


@app.command("list")
def list_bundles(
    templates_dir: Path | None = typer.Option(
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
    templates_dir: Path | None = typer.Option(
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


if __name__ == "__main__":
    app()
