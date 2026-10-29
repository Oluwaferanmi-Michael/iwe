"""Jinja2 template compilation engine and payload validation.

This module is responsible for parsing input payloads (from filesystem paths or
inline JSON strings), validating them against Pydantic schemas, and compiling
HTML markup using Jinja2 with custom domain formatting filters.
"""

from datetime import date, datetime
import json
from pathlib import Path
from typing import Any, Type
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel, ValidationError

from iwe.bundle import TemplateBundle


def load_payload_data(source: str) -> dict[str, Any]:
    """Load JSON payload from either a local file path or an inline JSON string.

    Args:
        source: A string pointing to an existing .json file path, or containing
            a raw JSON string (e.g. '{"key": "value"}').

    Returns:
        dict[str, Any]: The parsed JSON data as a Python dictionary.

    Raises:
        ValueError: If the file cannot be read, contains malformed JSON, or the
            string is neither a valid file path nor valid JSON.
    """
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
    """Validate a raw dictionary payload against a Pydantic Schema model class.

    Args:
        data: The unvalidated dictionary payload.
        schema_cls: The Pydantic model subclass defining the data contract.

    Returns:
        BaseModel: The validated Pydantic model instance.

    Raises:
        ValidationError: If the payload violates field types, missing required
            attributes, or fails custom model validators.
    """
    return schema_cls.model_validate(data)


def filter_currency(value: Any, symbol: str = "$", decimals: int = 2) -> str:
    """Jinja2 filter to format numeric values as currency strings.

    Args:
        value: Numeric value (float, int, or numeric string).
        symbol: Currency symbol prefix (default: "$").
        decimals: Decimal precision places (default: 2).

    Returns:
        str: Formatted currency string (e.g., "$1,250.00").
    """
    try:
        val = float(value)
        return f"{symbol}{val:,.{decimals}f}"
    except (ValueError, TypeError):
        return f"{symbol}{value}"


def filter_dateformat(value: Any, fmt: str = "%B %d, %Y") -> str:
    """Jinja2 filter to format dates, datetimes, or ISO date strings.

    Args:
        value: A date, datetime, or ISO 8601 formatted string.
        fmt: strftime format pattern (default: "%B %d, %Y").

    Returns:
        str: Formatted human-readable date string.
    """
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
    """Jinja2 filter to format numbers with thousand separators.

    Args:
        value: Numeric value (float, int, or numeric string).
        decimals: Number of decimal places. If 0, rounds to integer.

    Returns:
        str: Formatted number string with commas (e.g. "10,420").
    """
    try:
        val = float(value)
        if decimals == 0:
            return f"{int(round(val)):,}"
        return f"{val:,.{decimals}f}"
    except (ValueError, TypeError):
        return str(value)


class TemplateCompiler:
    """Compiles a template bundle's HTML using Jinja2 with validated payload data.

    Attributes:
        bundle: The TemplateBundle being compiled.
        env: The scoped Jinja2 Environment with custom filters registered.
    """

    def __init__(self, bundle: TemplateBundle) -> None:
        """Initialize the compiler for a specific template bundle.

        Args:
            bundle: The template bundle providing template.html and assets.

        Raises:
            FileNotFoundError: If the bundle directory does not contain template.html.
        """
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
        """Render template.html with the provided payload data.

        Args:
            payload: Validated Pydantic model instance or dictionary.

        Returns:
            str: Compiled HTML ready for rendering.
        """
        if isinstance(payload, BaseModel):
            context = payload.model_dump()
        else:
            context = dict(payload)

        # Inject base bundle path and metadata helpers
        context["_bundle_name"] = self.bundle.name
        context["_bundle_dir"] = str(self.bundle.path.resolve())

        template = self.env.get_template("template.html")
        return template.render(**context)
