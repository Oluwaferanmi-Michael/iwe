import tempfile
from pathlib import Path
from typing import Any
from playwright.sync_api import sync_playwright


class PdfRenderError(Exception):
    """Raised when PDF rendering via Playwright fails."""
    pass


class PdfRenderer:
    """Renders compiled HTML to PDF using Playwright headless Chromium."""

    def render(
        self,
        html_content: str,
        output_path: Path,
        base_dir: Path,
        config: dict[str, Any] | None = None,
        ready_selector: str = "#render-ready",
    ) -> Path:
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

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Write HTML temporarily into base_dir so relative assets (images/CSS) resolve properly
                temp_file = base_dir / f"_temp_render_{output_path.stem}.html"
                try:
                    temp_file.write_text(html_content, encoding="utf-8")
                    page.goto(temp_file.as_uri(), wait_until="networkidle")

                    # Check for explicit render-ready selector
                    try:
                        # If selector is present in HTML, wait for it
                        if ready_selector in html_content:
                            page.wait_for_selector(ready_selector, timeout=5000)
                    except Exception:
                        pass  # Proceed if timeout, networkidle already satisfied

                    page.pdf(**pdf_options)
                finally:
                    if temp_file.exists():
                        try:
                            temp_file.unlink()
                        except OSError:
                            pass
                browser.close()

            return output_path
        except Exception as e:
            raise PdfRenderError(f"Playwright rendering failed: {e}") from e
