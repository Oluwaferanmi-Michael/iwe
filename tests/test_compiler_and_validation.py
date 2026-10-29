import json
from pathlib import Path
import pytest
from pydantic import BaseModel, ValidationError

from iwe.bundle import TemplateBundle
from iwe.compiler import TemplateCompiler, load_payload_data, validate_payload


class SampleSchema(BaseModel):
    title: str
    amount: float
    items: list[str]


def test_load_payload_data_from_file(tmp_path: Path):
    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps({"title": "From File", "amount": 10.5, "items": ["a"]}), encoding="utf-8")
    loaded = load_payload_data(str(data_file))
    assert loaded["title"] == "From File"
    assert loaded["amount"] == 10.5


def test_load_payload_data_from_json_string():
    raw_json = '{"title": "Inline", "amount": 99.9, "items": ["x", "y"]}'
    loaded = load_payload_data(raw_json)
    assert loaded["title"] == "Inline"
    assert loaded["items"] == ["x", "y"]


def test_load_payload_data_invalid_json():
    with pytest.raises(ValueError, match="Invalid JSON payload"):
        load_payload_data('{"bad_json":')


def test_validate_payload_success():
    raw = {"title": "Test Report", "amount": 1500.5, "items": ["Alpha", "Beta"]}
    validated = validate_payload(raw, SampleSchema)
    assert validated.title == "Test Report"
    assert validated.amount == 1500.5


def test_validate_payload_failure():
    raw = {"title": "Missing amount and items"}
    with pytest.raises(ValidationError):
        validate_payload(raw, SampleSchema)


def test_compile_template_with_filters_and_data(tmp_path: Path):
    bundle_dir = tmp_path / "test-bundle"
    bundle_dir.mkdir(parents=True)
    template_content = """
    <h1>{{ title }}</h1>
    <p>Total: {{ amount | currency }}</p>
    <ul>
    {% for item in items %}
      <li>{{ item }}</li>
    {% endfor %}
    </ul>
    """
    (bundle_dir / "template.html").write_text(template_content, encoding="utf-8")
    (bundle_dir / "schema.py").write_text("from pydantic import BaseModel\nclass Schema(BaseModel):\n    title: str\n    amount: float\n    items: list[str]\n", encoding="utf-8")

    bundle = TemplateBundle(name="test-bundle", path=bundle_dir)
    compiler = TemplateCompiler(bundle)
    rendered_html = compiler.compile({"title": "Annual Report", "amount": 250000.0, "items": ["Revenue", "Profit"]})

    assert "<h1>Annual Report</h1>" in rendered_html
    assert "$250,000.00" in rendered_html
    assert "<li>Revenue</li>" in rendered_html
    assert "<li>Profit</li>" in rendered_html
