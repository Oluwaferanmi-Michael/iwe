# iwe

A Python-based CLI tool and engine for generating PDF documents from modular template bundles and validated data payloads using headless Chromium.

## Language

**Template Bundle**:
A self-contained directory containing the HTML markup, Jinja2 logic, Pydantic schema, static assets, and configuration for a single document type.
_Avoid_: Template folder, theme pack

**Template**:
The `template.html` file inside a template bundle containing HTML structure, CSS styling, and Jinja2 syntax.
_Avoid_: Layout, view

**Payload**:
The input data dictionary validated against a template bundle's schema before being injected into the template context.
_Avoid_: Context, params, arguments, variables

**Schema**:
The Pydantic data model defined in `schema.py` specifying the required and optional fields for a template bundle.
_Avoid_: Contract, DTO, serializer

**Renderer**:
The Playwright-based headless Chromium engine that loads rendered HTML and prints it to PDF.
_Avoid_: Converter, printer, compiler

**Generated Document**:
The resulting output PDF file written to the local `generated/` directory.
_Avoid_: Export, printout, report

**Preview**:
A local developer workflow that opens the compiled HTML in a visible browser window for rapid template iteration without emitting a PDF.
_Avoid_: Mock view, test render

**Render Ready Signal**:
An optional DOM selector or window condition that dynamic templates use to inform the renderer that asynchronous assets (fonts, charts) have fully completed rendering.
_Avoid_: Done trigger, finish hook

**Bundle Scaffolding**:
The automated generation of a new, minimal runnable Template Bundle (`template.html`, `schema.py`, `config.json`, `sample.json`, `assets/`) via `iwe new`.
_Avoid_: Template cloning, boilerplate generation

**Templates Directory**:
The directory resolved by `iwe` (via `--templates-dir`, `IWE_TEMPLATES_DIR`, `./iwe-templates`, or user fallback) where Template Bundles are discovered and stored.
_Avoid_: Bundle root, theme path

**Agent Skill**:
The standardized instructions and metadata (`SKILL.md`) enabling AI coding assistants to author bundles, validate schemas, and generate documents autonomously.
_Avoid_: Agent prompt, LLM context
