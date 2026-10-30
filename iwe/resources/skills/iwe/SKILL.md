---
name: iwe
description: Generate publication-grade PDF documents, author external HTML/Jinja2 template bundles, validate Pydantic schemas, or preview layouts using the iwe CLI engine. Use whenever creating PDF templates, generating PDFs from data, or running iwe commands.
---

# iwe PDF Generation Engine & Template Authoring

`iwe` is a command-line tool and Python engine for compiling publication-grade PDF documents from external HTML/Jinja2 template bundles and validated data payloads using Playwright (Chromium).

## Core Concepts

Always use canonical domain terminology:
- **Template Bundle**: Self-contained directory in the active templates directory (e.g. `./iwe-templates/<name>/`) containing `template.html`, `schema.py`, `config.json`, `sample.json`, and optional `assets/`.
- **Payload**: JSON input validated against the bundle's Pydantic schema before template rendering.
- **Renderer**: The headless Chromium print engine.
- **Render Ready Signal**: `#render-ready` DOM element or `window.__RENDER_READY__` flag for dynamic templates with async charts or webfonts.

## Workflow 1: Authoring a New Template Bundle

Follow this sequence in order:

### 1. Scaffold the bundle
Run the scaffolding command:
```bash
iwe new <bundle_name>
```
This generates the minimal valid bundle under the active templates directory (`./iwe-templates/<bundle_name>/`).

### 2. Define the Schema (`schema.py`)
Subclass `pydantic.BaseModel` naming the class exactly `Schema`. Use typed fields with descriptions and validation:
```python
from pydantic import BaseModel, Field

class Schema(BaseModel):
    title: str = Field(..., description="Document heading")
    author: str = Field(default="Anonymous")
    items: list[dict] = Field(default_factory=list)
```

### 3. Build HTML & Print CSS (`template.html`)
Follow strict print CSS rules:
- **Page settings**: Configure `@page { size: A4 portrait; margin: 15mm; }`.
- **Colors**: Force background colors and borders in print via `-webkit-print-color-adjust: exact; print-color-adjust: exact;`.
- **Page breaks**: Use `break-after: page;` for section breaks and `break-inside: avoid;` on table rows, cards, or signature blocks to prevent awkward splits.
- **Dynamic assets / Fonts**: If using Google Fonts or client-side charts (Chart.js, Vega), set `id="render-ready"` on a container once loaded so the renderer waits before printing.

### 4. Provide Sample Payload (`sample.json`)
Provide realistic mock data satisfying all required fields in `schema.py`.

### 5. Verify & Preview
Run sample inspection and browser preview:
```bash
iwe sample <bundle_name>
iwe preview <bundle_name> --data path/to/sample.json
```

**Completion Criterion**: `iwe preview` renders cleanly in the browser without schema or compilation errors.

---

## Workflow 2: Generating a PDF Document

To produce a production PDF:

```bash
# Generate from file payload
iwe generate <bundle_name> --data payload.json --output generated/output.pdf

# Generate from inline JSON
iwe generate <bundle_name> --data '{"title": "Invoice #1024"}'

# Override print settings directly via CLI
iwe generate <bundle_name> --data payload.json --format Letter --landscape --margin 12mm
```

### Automation & Scripting (`--json`)
Append `--json` to any command for structured JSON output on stdout/stderr:
```bash
iwe generate invoice --data payload.json --json
```

Output:
```json
{"status": "success", "document_path": "C:\\path\\to\\generated\\invoice-20261029.pdf", "bundle": "invoice"}
```

---

## Command Reference

| Command | Usage | Description |
|---|---|---|
| `iwe list` | `iwe list [-t <dir>] [--json]` | List discovered template bundles |
| `iwe new` | `iwe new <name> [-t <dir>] [-i]` | Scaffold a new minimal runnable template bundle |
| `iwe sample` | `iwe sample <name> [-t <dir>]` | Output the bundle's `sample.json` |
| `iwe preview` | `iwe preview <name> -d <data> [--no-open]` | Preview compiled HTML in browser |
| `iwe generate` | `iwe generate <name> -d <data> [-o <out>]` | Print publication-grade PDF |
| `iwe guide` | `iwe guide [--export <dir>]` | Display or export documentation |
| `iwe skill install` | `iwe skill install` | Install this agent skill into `.agents/skills/iwe` |

## Exit Codes
- `0`: Success.
- `1`: Validation error, missing bundle, or bad input payload.
- `2`: Renderer / Playwright execution error.
