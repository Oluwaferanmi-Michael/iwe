"""Template bundle discovery, metadata extraction, and dynamic schema loader.

This module provides classes for locating, inspecting, and loading colocated
template bundles stored under the templates/ directory. Each bundle encapsulates
an HTML/Jinja2 template, a Pydantic validation schema, page configurations,
sample mock data, and static assets.
"""

import importlib.util
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Type
from pydantic import BaseModel


class BundleNotFoundError(Exception):
    """Raised when a requested template bundle directory cannot be found on the filesystem."""
    pass


class SchemaLoadError(Exception):
    """Raised when a bundle's schema.py fails to load, cannot be imported, or lacks a Schema class."""
    pass


def resolve_templates_dir(custom_path: Path | None = None, prefer_creation: bool = False) -> Path:
    """Resolve the active templates directory based on four-tier precedence:

    1. Explicit custom path argument / CLI option.
    2. IWE_TEMPLATES_DIR environment variable.
    3. Local workspace ./iwe-templates if it exists.
    4. Local workspace ./templates if it exists (legacy compatibility).
    5. User home directory ~/.iwe/templates (or ./iwe-templates if prefer_creation is True).

    Args:
        custom_path: Explicit directory path passed by caller.
        prefer_creation: If True and no existing directory matches, returns ./iwe-templates.

    Returns:
        Path: The resolved directory path.
    """
    if custom_path is not None:
        return custom_path

    env_dir = os.environ.get("IWE_TEMPLATES_DIR")
    if env_dir:
        return Path(env_dir)

    local_iwe = Path.cwd() / "iwe-templates"
    if local_iwe.is_dir():
        return local_iwe

    local_legacy = Path.cwd() / "templates"
    if local_legacy.is_dir():
        return local_legacy

    if prefer_creation:
        return local_iwe

    user_home_templates = Path.home() / ".iwe" / "templates"
    if user_home_templates.is_dir():
        return user_home_templates

    return local_iwe


@dataclass
class TemplateBundle:
    """Represents a self-contained template bundle on disk.

    Attributes:
        name: The unique slug identifier of the template bundle (directory name).
        path: The absolute or relative filesystem path to the bundle directory.
    """
    name: str
    path: Path

    @property
    def template_path(self) -> Path:
        """Return path to template.html inside the bundle."""
        return self.path / "template.html"

    @property
    def schema_path(self) -> Path:
        """Return path to schema.py inside the bundle."""
        return self.path / "schema.py"

    @property
    def config_path(self) -> Path:
        """Return path to config.json inside the bundle."""
        return self.path / "config.json"

    @property
    def sample_path(self) -> Path:
        """Return path to sample.json inside the bundle."""
        return self.path / "sample.json"

    @property
    def assets_path(self) -> Path:
        """Return path to the assets/ subfolder inside the bundle."""
        return self.path / "assets"

    @property
    def has_template(self) -> bool:
        """Check if template.html exists as a file."""
        return self.template_path.is_file()

    @property
    def has_schema(self) -> bool:
        """Check if schema.py exists as a file."""
        return self.schema_path.is_file()

    @property
    def has_config(self) -> bool:
        """Check if config.json exists as a file."""
        return self.config_path.is_file()

    @property
    def has_sample(self) -> bool:
        """Check if sample.json exists as a file."""
        return self.sample_path.is_file()

    def get_schema_class(self) -> Type[BaseModel]:
        """Dynamically load and return the Pydantic Schema class from schema.py.

        Returns:
            Type[BaseModel]: The Pydantic model subclass named `Schema` declared
                in the bundle's schema.py.

        Raises:
            SchemaLoadError: If schema.py does not exist, fails module compilation,
                lacks a `Schema` attribute, or `Schema` does not subclass `BaseModel`.
        """
        if not self.has_schema:
            raise SchemaLoadError(f"Bundle '{self.name}' has no schema.py")

        module_name = f"iwe_bundle_{self.name.replace('-', '_')}_schema"
        spec = importlib.util.spec_from_file_location(module_name, self.schema_path)
        if spec is None or spec.loader is None:
            raise SchemaLoadError(f"Failed to load spec for {self.schema_path}")

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            raise SchemaLoadError(f"Error executing {self.schema_path}: {e}") from e

        if not hasattr(module, "Schema"):
            raise SchemaLoadError(f"{self.schema_path} does not define a 'Schema' class")

        schema_cls = getattr(module, "Schema")
        if not issubclass(schema_cls, BaseModel):
            raise SchemaLoadError(f"'Schema' in {self.schema_path} must subclass pydantic.BaseModel")

        return schema_cls

    def get_config(self) -> dict[str, Any]:
        """Read and parse print configuration from config.json.

        Returns:
            dict[str, Any]: Parsed JSON dictionary representing page format,
                margins, and header/footer options. Returns empty dict if absent.

        Raises:
            ValueError: If config.json exists but contains invalid JSON.
        """
        if not self.has_config:
            return {}
        try:
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ValueError(f"Invalid JSON in config.json for bundle '{self.name}': {e}") from e

    def get_sample_data(self) -> dict[str, Any]:
        """Read and parse representative mock payload from sample.json.

        Returns:
            dict[str, Any]: Parsed JSON dictionary of sample payload data.

        Raises:
            FileNotFoundError: If sample.json does not exist.
            ValueError: If sample.json contains invalid JSON syntax.
        """
        if not self.has_sample:
            raise FileNotFoundError(f"Bundle '{self.name}' has no sample.json")
        try:
            return json.loads(self.sample_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ValueError(f"Invalid JSON in sample.json for bundle '{self.name}': {e}") from e


class BundleManager:
    """Manages discovery and retrieval of template bundles across the filesystem.

    Attributes:
        templates_dir: The root directory searched for template bundles.
    """

    def __init__(self, templates_dir: Path | None = None) -> None:
        """Initialize BundleManager with an optional custom templates directory.

        Args:
            templates_dir: Path to directory containing bundles. If omitted,
                resolved via 4-tier precedence: custom -> IWE_TEMPLATES_DIR ->
                ./iwe-templates -> ./templates -> ~/.iwe/templates.
        """
        self.templates_dir = resolve_templates_dir(templates_dir)

    def list_bundles(self) -> list[TemplateBundle]:
        """Scan the templates directory and return all discovered bundles.

        Returns:
            list[TemplateBundle]: Sorted list of template bundles found on disk.
        """
        if not self.templates_dir.exists() or not self.templates_dir.is_dir():
            return []

        bundles = []
        for item in sorted(self.templates_dir.iterdir()):
            if item.is_dir() and not item.name.startswith((".", "_")):
                bundles.append(TemplateBundle(name=item.name, path=item))
        return bundles

    def get_bundle(self, name: str) -> TemplateBundle:
        """Retrieve a specific template bundle by directory name.

        Args:
            name: The directory name / slug of the template bundle.

        Returns:
            TemplateBundle: The matched template bundle object.

        Raises:
            BundleNotFoundError: If no directory matching `name` exists under templates_dir.
        """
        bundle_path = self.templates_dir / name
        if not bundle_path.exists() or not bundle_path.is_dir():
            raise BundleNotFoundError(f"Template bundle '{name}' not found at {bundle_path}")
        return TemplateBundle(name=name, path=bundle_path)
