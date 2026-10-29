from datetime import date, datetime
import json
from pathlib import Path
from typing import Any, Type
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel, ValidationError

from iwe.bundle import TemplateBundle


def load_payload_data(source: str) -> dict[str, Any]:
    """Load JSON payload from either a file path or an inline JSON string."""
    candidate_path = Path(source)
    if candidate_path.is_file():
        try:
            content = candidate_path.read_text(encoding="utf-8")
            return json.loads(content)
        except Exception as e:
            raise ValueError(f"Failed to read JSON payload from file '{source}': {e}") from e

    # Attempt parsing as raw inline JSON
    trimmed = source.strip()
    if trimmed.startswith("{") or trimmed.startswith("["):
        try:
            return json.loads(trimmed)
        except Exception as e:
            raise ValueError(f"Invalid JSON payload: {e}") from e

    raise ValueError(f"Payload '{source}' is neither an existing file nor a valid JSON string.")


def validate_payload(data: dict[str, Any], schema_cls: Type[BaseModel]) -> BaseModel:
    """Validate a dictionary payload against a Pydantic schema class."""
    return schema_cls.model_validate(data)


def filter_currency(value: Any, symbol: str = "$", decimals: int = 2) -> str:
    """Format numeric values as currency strings (e.g. $1,250.00)."""
    try:
        val = float(value)
        return f"{symbol}{val:,.{decimals}f}"
    except (ValueError, TypeError):
        return f"{symbol}{value}"


def filter_dateformat(value: Any, fmt: str = "%B %d, %Y") -> str:
    """Format date/datetime objects or ISO date strings."""
    if isinstance(value, (datetime, date)):
        return value.strftime(fmt)
    if isinstance(value, str):
        for parse_fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(value.split(".")[0].rstrip("Z"), parse_fmt)
                return dt.strftime(fmt)
            except ValueError:
                continue
    return str(value)


def filter_number(value: Any, decimals: int = 0) -> str:
    """Format numbers with thousands separators and decimal precision."""
    try:
        val = float(value)
        if decimals == 0:
            return f"{int(round(val)):,}"
        return f"{val:,.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)


class TemplateCompiler:
    """Compiles a template bundle's HTML using Jinja2 with validated payload data."""

    def __init__(self, bundle: TemplateBundle) -> None:
        self.bundle = bundle
        if not self.bundle.has_template:
            raise FileNotFoundError(f"Template bundle '{self.bundle.name}' missing template.html at {self.bundle.template_path}")

        self.env = Environment(
            loader=FileSystemLoader(self.bundle.path),
            autoescape=select_autoescape(["html", "xml"]),
        )
        self.env.filters["currency"] = filter_currency
        self.env.filters["dateformat"] = filter_dateformat
        self.env.filters["number"] = filter_number

    def compile(self, payload: dict[str, Any] | BaseModel) -> str:
        """Render template.html with the given payload."""
        if isinstance(payload, BaseModel):
            context = payload.model_dump()
        else:
            context = dict(payload)

        # Inject base bundle path and metadata helpers
        context["_bundle_name"] = self.bundle.name
        context["_bundle_dir"] = str(self.bundle.path.resolve())

        template = self.env.get_template("template.html")
        return template.render(**context)
