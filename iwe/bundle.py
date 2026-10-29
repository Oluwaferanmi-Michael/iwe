import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Type
from pydantic import BaseModel


class BundleNotFoundError(Exception):
    """Raised when a template bundle cannot be found."""
    pass


class SchemaLoadError(Exception):
    """Raised when schema.py cannot be loaded or lacks Schema model."""
    pass


@dataclass
class TemplateBundle:
    name: str
    path: Path

    @property
    def template_path(self) -> Path:
        return self.path / "template.html"

    @property
    def schema_path(self) -> Path:
        return self.path / "schema.py"

    @property
    def config_path(self) -> Path:
        return self.path / "config.json"

    @property
    def sample_path(self) -> Path:
        return self.path / "sample.json"

    @property
    def assets_path(self) -> Path:
        return self.path / "assets"

    @property
    def has_template(self) -> bool:
        return self.template_path.is_file()

    @property
    def has_schema(self) -> bool:
        return self.schema_path.is_file()

    @property
    def has_config(self) -> bool:
        return self.config_path.is_file()

    @property
    def has_sample(self) -> bool:
        return self.sample_path.is_file()

    def get_schema_class(self) -> Type[BaseModel]:
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
        if not self.has_config:
            return {}
        try:
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ValueError(f"Invalid JSON in config.json for bundle '{self.name}': {e}") from e

    def get_sample_data(self) -> dict[str, Any]:
        if not self.has_sample:
            raise FileNotFoundError(f"Bundle '{self.name}' has no sample.json")
        try:
            return json.loads(self.sample_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ValueError(f"Invalid JSON in sample.json for bundle '{self.name}': {e}") from e


class BundleManager:
    def __init__(self, templates_dir: Path | None = None) -> None:
        self.templates_dir = templates_dir or (Path.cwd() / "templates")

    def list_bundles(self) -> list[TemplateBundle]:
        if not self.templates_dir.exists() or not self.templates_dir.is_dir():
            return []
        
        bundles = []
        for item in sorted(self.templates_dir.iterdir()):
            if item.is_dir() and not item.name.startswith((".", "_")):
                bundles.append(TemplateBundle(name=item.name, path=item))
        return bundles

    def get_bundle(self, name: str) -> TemplateBundle:
        bundle_path = self.templates_dir / name
        if not bundle_path.exists() or not bundle_path.is_dir():
            raise BundleNotFoundError(f"Template bundle '{name}' not found at {bundle_path}")
        return TemplateBundle(name=name, path=bundle_path)
