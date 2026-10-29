"""Playwright headless Chromium rendering engine for printing HTML to PDF.

This module automates headless Chromium via Playwright, providing sandboxed
execution, relative asset resolution via base URI injection, and dual
render-readiness synchronization before snapshotting pages to PDF.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Any
from playwright.sync_api import sync_playwright


class PdfRenderError(Exception):
    """Raised when PDF rendering or Playwright browser execution fails."""
    pass


class PdfRenderer:
    """Renders compiled HTML documents to PDF using Playwright headless Chromium.

    Handles headless browser lifecycle, isolated filesystem sandboxing,
    relative stylesheet and image resolution, and dynamic readiness gates.
    """

    def render(
        self,
        html_content: str,
        output_path: Path,
        base_dir: Path,
        config: dict[str, Any] | None = None,
        ready_selector: str = "#render-ready",
    ) -> Path:
        """Render an HTML string to a PDF file on disk.

        Args:
            html_content: The compiled HTML markup to render.
            output_path: Destination path where the PDF will be saved.
            base_dir: Path to the template bundle directory for relative asset resolution.
            config: Optional print configuration dictionary (format, landscape, margins, headers/footers).
            ready_selector: CSS selector to optionally wait for before capturing PDF. Defaults to '#render-ready'.

        Returns:
            Path: The resolved absolute path of the generated PDF document.

        Raises:
            PdfRenderError: If Playwright fails to launch, the page throws a critical
                navigation error, or the PDF generation fails.
        """
        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        config = config or {}

        # Merge defaults with config
        pdf_options: dict[str, Any] = {
            "path": str(output_path),
            "format": config.get("format", "A4"),
            "landscape": config.get("landscape", False),
            "print_background": config.get("print_background", True),
        }

        if "margin" in config and isinstance(config["margin"], dict):
            pdf_options["margin"] = config["margin"]

        if "scale" in config:
            pdf_options["scale"] = config["scale"]

        if "header_template" in config or "footer_template" in config:
            pdf_options["display_header_footer"] = True
            if "header_template" in config:
                pdf_options["header_template"] = config["header_template"]
            if "footer_template" in config:
                pdf_options["footer_template"] = config["footer_template"]

        # Inject base href so relative assets resolve against the template bundle directory
        base_uri = base_dir.resolve().as_uri() + "/"
        base_tag = f'<base href="{base_uri}">'
        if "<head>" in html_content:
            prepared_html = html_content.replace("<head>", f"<head>\n    {base_tag}", 1)
        else:
            prepared_html = f"<head>{base_tag}</head>\n" + html_content

        temp_dir = Path(tempfile.mkdtemp(prefix="iwe_render_"))
        temp_file = temp_dir / "index.html"

        try:
            temp_file.write_text(prepared_html, encoding="utf-8")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Navigate to the HTML file in isolated temp dir with networkidle wait
                page.goto(temp_file.as_uri(), wait_until="networkidle")

                # Dynamic dual render-readiness evaluation per ADR 0003
                # Checks for window.__RENDER_READY__ === true OR #render-ready element in DOM
                custom_selector = config.get("ready_selector", ready_selector)
                ready_timeout = config.get("ready_timeout_ms", 3000)
                try:
                    page.wait_for_function(
                        f"""() => {{
                            if (window.__RENDER_READY__ === true) return true;
                            if (document.querySelector('{custom_selector}')) return true;
                            return false;
                        }}""",
                        timeout=ready_timeout,
                    )
                except Exception:
                    # networkidle is already satisfied; proceed with PDF capture
                    pass

                page.pdf(**pdf_options)
                browser.close()

            return output_path
        except Exception as e:
            raise PdfRenderError(f"Playwright rendering failed: {e}") from e
        finally:
            # Clean up temporary render folder
            if temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception:
                    pass
