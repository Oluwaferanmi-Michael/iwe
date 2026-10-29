# Template Authoring Guide

This guide walks you through creating, styling, and configuring custom template bundles for `iwe`.

---

## What is a Template Bundle?

In `iwe`, a **Template Bundle** is a self-contained directory under `templates/<bundle_name>/` that packages everything needed to produce a specific type of document:

```
templates/invoice/
├── template.html      # HTML markup, CSS styling, and Jinja2 templating syntax
├── schema.py          # Pydantic Schema model enforcing data requirements
├── config.json        # Page format, margins, and header/footer templates
├── sample.json        # Representative mock data for testing
└── assets/            # Optional static files (logos, custom fonts, images)
```

By colocating these files, each document type can be developed, tested, and distributed in complete isolation.

---

## Step-by-Step: Creating a New Bundle

### Step 1: Create the Bundle Directory
Choose a slug name (e.g. `receipt` or `tax-summary`):
```bash
mkdir -p templates/receipt/assets
```

### Step 2: Define `schema.py`
Inside `templates/receipt/schema.py`, create a Pydantic model named `Schema`:

```python
from typing import List, Optional
from pydantic import BaseModel, Field

class ReceiptItem(BaseModel):
    description: str
    quantity: int = 1
    unit_price: float

class Schema(BaseModel):
    receipt_number: str
    customer_name: str
    date: str
    items: List[ReceiptItem] = Field(default_factory=list)
    tax_rate: float = 0.08
    notes: Optional[str] = None
```

> **Rule**: The root model class **must** be named `Schema` and inherit from `pydantic.BaseModel`.

### Step 3: Provide `config.json`
Set default page layout and margins in `templates/receipt/config.json`:

```json
{
  "format": "A4",
  "landscape": false,
  "print_background": true,
  "margin": {
    "top": "15mm",
    "bottom": "15mm",
    "left": "15mm",
    "right": "15mm"
  },
  "footer_template": "<div style=\"font-size: 8px; color: #718096; width: 100%; text-align: center;\">Page <span class=\"pageNumber\"></span> of <span class=\"totalPages\"></span></div>"
}
```

#### Available Config Options:
- **`format`**: Standard paper size (`A4`, `Letter`, `Legal`, `Tabloid`, `A3`, `A5`).
- **`landscape`**: `true` for landscape, `false` for portrait.
- **`print_background`**: `true` to print CSS background colors and images.
- **`margin`**: Object with `top`, `bottom`, `left`, `right` (e.g., `"10mm"`, `"0.5in"`).
- **`header_template`**: HTML for running page headers. Supports `<span class="pageNumber"></span>`, `<span class="totalPages"></span>`, `<span class="date"></span>`, and `<span class="title"></span>`.
- **`footer_template`**: HTML for running page footers.

### Step 4: Provide `sample.json`
Provide a realistic mock payload matching your schema in `templates/receipt/sample.json`:

```json
{
  "receipt_number": "REC-2026-0042",
  "customer_name": "Jane Doe",
  "date": "2026-10-28",
  "items": [
    {
      "description": "Standard Cloud Subscription",
      "quantity": 1,
      "unit_price": 49.00
    },
    {
      "description": "Additional Storage 100GB",
      "quantity": 2,
      "unit_price": 10.00
    }
  ],
  "tax_rate": 0.08,
  "notes": "Thank you for your business!"
}
```

### Step 5: Write `template.html`
In `templates/receipt/template.html`, structure your document with HTML, CSS, and Jinja2 expressions:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Receipt {{ receipt_number }}</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: #2d3748;
      padding: 10mm;
    }
    h1 {
      color: #2b6cb0;
      margin-bottom: 8px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
    }
    th, td {
      padding: 8px 12px;
      border-bottom: 1px solid #e2e8f0;
      text-align: left;
    }
    th {
      background-color: #f7fafc;
    }
    .text-right {
      text-align: right;
    }
  </style>
</head>
<body>
  <h1>Receipt {{ receipt_number }}</h1>
  <p><strong>Customer:</strong> {{ customer_name }}</p>
  <p><strong>Date:</strong> {{ date | dateformat }}</p>

  <table>
    <thead>
      <tr>
        <th>Item</th>
        <th class="text-right">Qty</th>
        <th class="text-right">Unit Price</th>
        <th class="text-right">Total</th>
      </tr>
    </thead>
    <tbody>
      {% for item in items %}
      <tr>
        <td>{{ item.description }}</td>
        <td class="text-right">{{ item.quantity }}</td>
        <td class="text-right">{{ item.unit_price | currency }}</td>
        <td class="text-right">{{ (item.quantity * item.unit_price) | currency }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  {% if notes %}
  <p style="margin-top: 20px; font-style: italic; color: #718096;">{{ notes }}</p>
  {% endif %}

  <!-- Render readiness signal -->
  <div id="render-ready"></div>
</body>
</html>
```

---

## Built-in Jinja2 Template Filters

`iwe` provides convenient formatting filters:

| Filter | Description | Example Input | Output |
| --- | --- | --- | --- |
| `currency` | Formats a number as currency | `{{ 1250.5 | currency }}` | `$1,250.50` |
| `currency(symbol="€")` | Custom currency symbol | `{{ 1250.5 | currency("€") }}` | `€1,250.50` |
| `dateformat` | Formats dates/ISO strings | `{{ "2026-10-28" | dateformat }}` | `October 28, 2026` |
| `number` | Thousand separators | `{{ 10420 | number }}` | `10,420` |
| `number(decimals=2)` | Precision formatting | `{{ 10420.556 | number(2) }}` | `10,420.56` |

---

## Print CSS & Multi-Page Layouts

### Page Breaks
Force a page break cleanly between sections:
```css
.page-break {
  page-break-after: always;
  break-after: page;
}
```

### Prevent Awkward Splitting
Prevent table rows or cards from being split across page boundaries:
```css
tr, .card, .chart-container {
  page-break-inside: avoid;
  break-inside: avoid;
}
```

---

## Render Readiness Strategy

If your template uses client-side JavaScript (e.g. rendering charts with Chart.js, rendering QR codes, or waiting for web fonts):

1. Put `<div id="render-ready"></div>` or trigger an element insertion when JavaScript finishes.
2. `iwe` automatically waits for `#render-ready` to ensure the PDF snapshot is taken only after all async graphics are completely drawn.

---

## Development Workflow

1. **Verify discovery**:
   ```bash
   iwe list
   ```
2. **Inspect sample data**:
   ```bash
   iwe sample <bundle_name>
   ```
3. **Interactive preview**:
   ```bash
   iwe preview <bundle_name> --data templates/<bundle_name>/sample.json
   ```
4. **Generate the PDF**:
   ```bash
   iwe generate <bundle_name> --data templates/<bundle_name>/sample.json
   ```
