# iwe CLI Guide

`iwe` is a command-line tool and engine for generating publication-quality PDF documents from modular template bundles and validated data payloads using Playwright (Chromium).

---

## Installation

### With pipx (Recommended for standalone CLI usage)
```bash
pipx install git+https://github.com/Oluwaferanmi-Michael/iwe.git
playwright install chromium
```

### With pip
```bash
pip install git+https://github.com/Oluwaferanmi-Michael/iwe.git
playwright install chromium
```

---

## Templates Directory Resolution

When locating template bundles, `iwe` searches in the following order of precedence:
1. `--templates-dir <path>` / `-t <path>` (CLI flag override)
2. `IWE_TEMPLATES_DIR` environment variable
3. `./iwe-templates/` (Current workspace directory)
4. `./templates/` (Current workspace legacy fallback)
5. `~/.iwe/templates/` (Global user home fallback)

---

## Commands Reference

### 1. `iwe new` (alias: `iwe scaffold`)
Scaffold a new runnable minimal Template Bundle:
```bash
# Non-interactive (default)
iwe new invoice

# Interactive prompt
iwe new invoice --interactive

# Specify custom templates directory
iwe new invoice -t ./my-templates
```
Creates:
- `schema.py`: Minimal Pydantic `Schema` class
- `config.json`: Default print configuration (A4, 10mm margins)
- `sample.json`: Valid mock JSON data
- `template.html`: Clean HTML5 boilerplate with print CSS and page numbers
- `assets/`: Static assets directory

### 2. `iwe list`
List all discovered template bundles:
```bash
iwe list
iwe list --json
```

### 3. `iwe sample <bundle_name>`
Print the mock payload for a bundle formatted as JSON:
```bash
iwe sample invoice
```

### 4. `iwe preview <bundle_name>`
Compile the template bundle with a payload and open it in a visible web browser:
```bash
# From file
iwe preview invoice --data ./data.json

# From inline JSON
iwe preview invoice --data '{"title": "Invoice #1"}'

# Without launching browser
iwe preview invoice --data ./data.json --no-open
```

### 5. `iwe generate <bundle_name>`
Compile and render a publication-grade PDF:
```bash
# Output defaults to generated/<bundle>-<timestamp>.pdf
iwe generate invoice --data ./data.json

# Custom output destination
iwe generate invoice --data ./data.json --output ./invoice.pdf

# Print overrides
iwe generate invoice --data ./data.json --format Letter --landscape --margin 15mm

# JSON output mode for automation
iwe generate invoice --data ./data.json --json
```

### 6. `iwe guide` (alias: `iwe docs`)
Display comprehensive documentation in the terminal or export it to files:
```bash
# Interactive terminal viewer
iwe guide

# View specific topic
iwe guide --topic templates
iwe guide --topic cli

# Export markdown guides to a directory
iwe guide --export ./docs
```

### 7. `iwe skill install`
Install the AI coding agent skill into `.agents/skills/iwe/SKILL.md`:
```bash
iwe skill install
```

---

## Exit Codes
- `0`: Success. Generated PDF path or result printed to stdout.
- `1`: Validation error, missing bundle, or payload error (printed to stderr).
- `2`: Playwright / Chromium rendering error.
