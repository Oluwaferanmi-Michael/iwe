# Specification: iwe PDF Generation System

## Problem Statement

Generating publication-quality PDF documents from dynamic application data is frustrating and error-prone. Existing solutions either use legacy rendering engines with poor or broken modern CSS support (leaving developers wrestling with outdated box models and missing flex/grid support) or force developers into cumbersome proprietary DSLs and rigid Python report builders. Developers and automated systems (including AI agents) need a simple, reliable command-line tool that can take a structured data payload, validate it against a contract, inject it into an HTML/CSS template with modern design capabilities, and produce a pixel-perfect PDF file locally.

## Solution

`iwe` is a command-line tool and Python engine that renders publication-grade PDF documents using headless Chromium and modular template bundles. Each document type is packaged as a self-contained bundle with its own Jinja2 HTML template, Pydantic schema, print configuration, static assets, and mock sample data. `iwe` validates the input payload before rendering, compiles the HTML, runs headless Chromium to render modern CSS and JavaScript charts, waits for render readiness, and writes the generated document to a local directory. It also provides interactive browser previews for template design, sample payload extraction, and clear documentation for both human operators and autonomous AI agents.

## User Stories

1. As a developer, I want to install `iwe` via standard Python package tooling, so that I can run the CLI from my terminal without manual path configuration.
2. As a developer, I want to run `iwe list`, so that I can see all available template bundles installed in the project.
3. As an AI agent or human operator, I want to read `AGENTS.md` and `README.md`, so that I understand the CLI commands, argument flags, and invocation patterns without needing trial and error.
4. As a developer, I want to run `iwe sample <bundle_name>`, so that I can inspect a valid sample payload that conforms to the bundle's schema.
5. As a developer, I want `iwe generate` to validate the input payload against the bundle's schema, so that malformed data is caught immediately with actionable validation errors before launching a browser.
6. As a developer, I want `iwe generate <bundle_name> --data payload.json` to compile the template and output a PDF to the local `generated/` directory, so that my generated document is saved reliably.
7. As a developer, I want to pass an inline JSON string via `--data '{"title": "Test"}'` to `iwe generate`, so that I can generate documents in shell pipelines without creating temporary JSON files.
8. As a developer, I want to specify a custom output destination with `--output <path>`, so that I can place generated documents wherever my workflow requires.
9. As a template designer, I want to run `iwe preview <bundle_name> --data payload.json`, so that I can open the rendered HTML directly in a visible browser for fast styling iteration.
10. As a template author, I want each document type to live as a self-contained template bundle with its own HTML, schema, configuration, and assets, so that I can create or modify document designs in complete isolation.
11. As a template author, I want relative asset paths (like images and fonts) inside the template bundle to resolve properly during rendering, so that I can include logos and stylesheets without base64 encoding.
12. As a template author, I want to configure page size, orientation, and margins via `config.json` inside the template bundle, so that document dimensions are standardized for that document type.
13. As a developer, I want to override page format or margins via CLI flags (e.g. `--format Letter`, `--landscape`), so that I can adapt the output without modifying the template files.
14. As a template author, I want multi-page reports to support repeating headers, footers, and dynamic page numbers, so that generated multi-page documents look professional.
15. As a template author, I want `iwe` to wait for asynchronous JavaScript (such as Chart.js or web fonts) to finish rendering before taking the PDF snapshot, so that charts and dynamic graphs never appear blank or clipped.
16. As an AI agent, I want `iwe` to emit predictable exit codes and structured console output (or JSON errors), so that I can programmatically detect whether generation succeeded or failed.
17. As a developer, I want a step-by-step Template Authoring Guide, so that I can easily create new template bundles with schemas and mock data.

## Implementation Decisions

### 1. Project Modules and Architecture
- **CLI Module**: Built using `Typer` and `Rich`, exposing `generate`, `preview`, `sample`, and `list` commands with colorized feedback, proper error exit codes, and comprehensive help descriptions.
- **Template Bundle Manager**: Responsible for scanning the `templates/` directory, dynamically loading each bundle's Pydantic `Schema`, reading its `config.json`, and providing sample payloads.
- **Compiler Module**: Uses `Jinja2` with a `FileSystemLoader` scoped to the active bundle directory. Injects validated payload attributes and template helper filters (e.g., date and currency formatting).
- **Renderer Module**: Leverages `Playwright` to launch headless Chromium, load compiled HTML using a local `file://` base path (guaranteeing relative asset resolution), wait for `networkidle` and optional `#render-ready` signals, and execute `page.pdf()` with specified print parameters.
- **Storage / Output Handler**: Ensures target directories (default `generated/`) exist and writes the generated document binary cleanly.

### 2. Documentation Architecture
- `README.md`: Human-facing documentation including a Quickstart guide, installation instructions, command reference, and configuration options.
- `AGENTS.md`: Agent-facing operational documentation specifying machine-readable CLI invocation patterns, input expectations, exit codes, and error recovery strategies.
- `docs/templates.md`: Template Authoring Guide detailing how to create a new template bundle, write a Pydantic schema, bind CSS print styles, configure `@page` rules, and emit render ready signals.

### 3. Starter Template Bundle: `multi-page-report`
- Colocated under `templates/multi-page-report/` containing:
  - `template.html`: Multi-page layout featuring a cover page, executive summary, key metrics badges, tabular data, a client-rendered CSS/SVG chart, and running header/footer with page numbers.
  - `schema.py`: Pydantic `Schema` model enforcing fields such as `report_title`, `subtitle`, `prepared_for`, `prepared_by`, `date`, `summary`, `metrics`, `sections`, and `table_data`.
  - `config.json`: Default print options (`format: "A4"`, `print_background: true`, `margin: {"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"}`).
  - `sample.json`: Realistic mock data to verify end-to-end generation out-of-the-box.
  - `assets/`: Styling and logo assets.

### 4. Architectural Rules and ADR Alignment
- Uses Playwright headless Chromium for full CSS/JS rendering power (`ADR 0001`).
- Uses colocated template bundles for modularity and isolation (`ADR 0002`).
- Uses dual render readiness detection (`ADR 0003`).
- Strictly adheres to the project domain vocabulary defined in `GLOSSARY.md`.

## Testing Decisions

### Test Quality Philosophy
- Tests must verify external observable behavior only, never private implementation details.
- Avoid mocking internal components; exercise the full path from input payload to generated PDF.

### Testing Seam
- **Primary Seam**: The **CLI Invocation Seam** using `typer.testing.CliRunner`.
  - Tests invoke commands like `iwe generate multi-page-report --data sample.json` and `iwe sample multi-page-report`.
  - Assertions verify command exit codes (0 for success, non-zero for validation/runtime failure), console output messages, and the physical presence of valid PDF files in `generated/` (verifying file existence, positive file size, and `%PDF-` header magic bytes).
  - Validation failures are tested by passing invalid JSON payloads to verify graceful CLI error handling without tracebacks.

### Prior Art
- Standard Typer and Click test harnesses using `CliRunner` with temporary directories (`tmp_path`) for output isolation.

## Out of Scope
- Hosting `iwe` as an HTTP REST API microservice (deferred to a future release per user decision).
- Asynchronous task queues (Celery/Redis).
- Cloud object storage uploads (AWS S3, Google Cloud Storage).
- WYSIWYG drag-and-drop template editors.
- Non-HTML template engines (e.g., LaTeX, Typst, ReportLab).

## Further Notes
- Python 3.10+ compatibility.
- Playwright browser binaries are installed via `playwright install chromium`.
