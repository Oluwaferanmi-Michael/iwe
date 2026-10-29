# Contributing to iwe

Thank you for your interest in contributing to **`iwe`**! This document provides guidelines and instructions for setting up a local development environment, running tests, following our architectural conventions, and submitting pull requests.

---

## 1. Prerequisites

Before working on `iwe`, ensure you have the following installed:
- **Python 3.10+**
- **Git**
- A terminal with standard shell or PowerShell

---

## 2. Local Development Setup

### Clone the Repository
```bash
git clone https://github.com/Oluwaferanmi-Michael/iwe.git
cd iwe
```

### Create and Activate a Virtual Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate on Linux/macOS:
source .venv/bin/activate

# Activate on Windows PowerShell:
.venv\Scripts\Activate.ps1
```

### Install Dependencies in Editable Mode
Install `iwe` in editable development mode along with development dependencies:
```bash
pip install -e ".[dev]"
```

### Install Playwright Chromium
`iwe` relies on Playwright headless Chromium for rendering:
```bash
playwright install chromium
```

Verify your setup:
```bash
iwe --help
pytest
```

---

## 3. Architecture & Domain Language

Before writing code, familiarize yourself with our project domain:
- **Architecture & Subsystems**: Read [`docs/architecture.md`](docs/architecture.md) for data flow and component boundaries.
- **Domain Vocabulary**: Read [`GLOSSARY.md`](GLOSSARY.md). Always use established project terms (`Template Bundle`, `Template`, `Payload`, `Schema`, `Renderer`, `Generated Document`, `Preview`, `Render Ready Signal`).
- **Architecture Decision Records**: Consult [`docs/adr/`](docs/adr/) for rationale on technical choices (Playwright Chromium, colocated bundles, dual render readiness).

---

## 4. Testing Guidelines

We enforce a strict testing philosophy:

- **Single High-Level Seam**: All tests in `tests/` should test external observable behavior through the CLI invocation seam using `typer.testing.CliRunner`.
- **No Private Method Mocks**: Avoid mocking internal methods or helpers. Test the full execution path from input payload to generated PDF artifact.
- **Verification Criteria**:
  - Exit codes: `0` for success, `1` for data/validation errors, `2` for Playwright rendering errors.
  - PDF binary validation: Assert that the resulting file exists and starts with the `%PDF-` header magic bytes.
  - Temporary directory isolation: Use pytest's `tmp_path` fixture for custom outputs so tests remain isolated and side-effect free.

### Running Tests
```bash
# Run full test suite
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_cli_generate.py
```

---

## 5. Adding a Template Bundle Checklist

When contributing a new template bundle:
1. Create `templates/<bundle_name>/`.
2. Provide `schema.py` containing a Pydantic model named `Schema` subclassing `pydantic.BaseModel`.
3. Provide `template.html` with clean HTML5, Jinja2 syntax, and print CSS (`@page` rules, `.page-break`).
4. Provide `config.json` specifying paper format, margins, and header/footer templates.
5. Provide `sample.json` with realistic test data satisfying `Schema`.
6. Include `<div id="render-ready"></div>` if client-side JavaScript or fonts require delayed snapshotting.
7. Verify your bundle using the CLI:
   ```bash
   iwe sample <bundle_name>
   iwe preview <bundle_name> --data templates/<bundle_name>/sample.json
   iwe generate <bundle_name> --data templates/<bundle_name>/sample.json
   ```

---

## 6. Pull Request & Commit Workflow

1. Fork or branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Write tests verifying your changes (red-green-refactor).
3. Ensure all tests pass: `pytest`.
4. Commit your changes using conventional prefixes (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
5. Open a Pull Request referencing the related issue (`Closes #<issue_number>`).
