# iwe

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **`iwe`** (Yoruba for *book*, *document*, or *paper*) is a command-line tool and Python engine for generating publication-quality PDF documents from external HTML/Jinja2 template bundles and validated data payloads using headless Chromium.

---

## Key Features

- **Modern Web Standards**: Full support for CSS Grid, Flexbox, web fonts, inline SVG, and modern typography powered by Playwright headless Chromium.
- **Strongly-Typed Contracts**: Every template bundle defines a Pydantic `Schema`. Payloads are strictly validated before launching the browser, catching errors before render time.
- **Modular Colocated Bundles**: Each document type lives in its own self-contained directory with its markup, schema, configuration, assets, and sample mock data.
- **Dual Render Readiness**: Waits for `networkidle` by default with support for an explicit `#render-ready` selector to ensure client-side charts and web fonts finish rendering before snapshotting.
- **Interactive Developer Preview**: Run `iwe preview` to open compiled templates with live mock data in your browser for rapid CSS/HTML tweaking.
- **Built-in Formatting Filters**: Standard Jinja2 filters for currency (`| currency`), dates (`| dateformat`), and numbers (`| number`).

---

## Installation

### Prerequisites
- Python 3.10 or higher
- Git

### 1. Clone the repository
```bash
git clone https://github.com/Oluwaferanmi-Michael/iwe.git
cd iwe
```

### 2. Create and activate a virtual environment
```bash
python -m venv .venv

# On Windows PowerShell:
.venv\Scripts\Activate.ps1

# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install `iwe` and Playwright Chromium
```bash
pip install -e .
playwright install chromium
```

Verify your installation:
```bash
iwe --help
```

---

## Quickstart

### 1. List installed template bundles
```bash
iwe list
```

### 2. Inspect a bundle's sample data payload
```bash
iwe sample multi-page-report
```

### 3. Generate a PDF document
Generate a document from the reference sample payload:
```bash
iwe generate multi-page-report --data templates/multi-page-report/sample.json
```
The output PDF is saved to `generated/multi-page-report-<timestamp>.pdf`.

You can also specify a custom output path:
```bash
iwe generate multi-page-report --data templates/multi-page-report/sample.json --output ./my_report.pdf
```

### 4. Generate from inline JSON
Pass JSON directly on the command line:
```bash
iwe generate multi-page-report --data '{"report_title": "Flash Update", ...}'
```

### 5. Interactive Browser Preview
Preview your template directly in a visible browser without generating a PDF:
```bash
iwe preview multi-page-report --data templates/multi-page-report/sample.json
```

---

## Command Reference

### `iwe list`
List all installed template bundles in `templates/` and their component status.

```bash
iwe list [--templates-dir <path>]
```

### `iwe sample <bundle_name>`
Print the mock payload for a given bundle formatted as JSON.

```bash
iwe sample multi-page-report
```

### `iwe generate <bundle_name> [OPTIONS]`
Compile the template with the provided payload and render it to a PDF.

| Option | Flag | Description |
| --- | --- | --- |
| `--data` | `-d` | **(Required)** Path to JSON payload file or inline JSON string |
| `--output` | `-o` | Custom file path for output PDF (default: `generated/<bundle>-<timestamp>.pdf`) |
| `--format` | `-f` | Page format override (e.g. `A4`, `Letter`, `Legal`) |
| `--landscape` | | Render in landscape orientation |
| `--templates-dir` | `-t` | Custom templates directory path |

### `iwe preview <bundle_name> [OPTIONS]`
Compile the template with the provided payload and open it in your web browser.

| Option | Flag | Description |
| --- | --- | --- |
| `--data` | `-d` | **(Required)** Path to JSON payload file or inline JSON string |
| `--open / --no-open` | | Automatically open system browser (default: true) |
| `--templates-dir` | `-t` | Custom templates directory path |

---

## Exit Codes for Automation & AI Agents

- **`0`**: Success. The generated PDF path is printed to stdout.
- **`1`**: Data validation error, missing bundle, or malformed input payload. Error details are printed to stderr.
- **`2`**: Playwright browser execution or PDF rendering error.

---

## Project Structure

```
iwe/
├── iwe/                       # Python application package
│   ├── __init__.py
│   ├── cli.py                 # Typer CLI application
│   ├── bundle.py              # Template bundle manager and discovery
│   ├── compiler.py            # Jinja2 template compiler and payload validation
│   └── renderer.py            # Playwright headless Chromium PDF printer
├── templates/                 # Modular template bundles
│   └── multi-page-report/     # Starter multi-page executive report bundle
│       ├── template.html      # HTML/Jinja2 template
│       ├── schema.py          # Pydantic validation model
│       ├── config.json        # PDF print settings (margins, header/footer)
│       └── sample.json        # Test payload
├── docs/
│   ├── templates.md           # Template Authoring Guide
│   ├── spec.md                # System specification
│   ├── adr/                   # Architecture Decision Records
│   └── agents/                # Machine/agent operational guidelines
├── generated/                 # Default destination for generated PDFs
├── pyproject.toml             # Package configuration & dependencies
└── GLOSSARY.md                # Project domain language definitions
```

---

## Creating New Templates

See [`docs/templates.md`](docs/templates.md) for a comprehensive step-by-step guide to authoring new template bundles, writing Pydantic validation schemas, designing CSS `@page` print styles, and signaling render readiness.
