import json
from pathlib import Path

from bright_smile.cli import build_openapi_schema, main


def test_schema_builds_without_environment() -> None:
    schema = build_openapi_schema()

    assert schema["info"]["title"] == "Bright Smile Dental AI Front Desk API"
    assert schema["paths"]["/api/health"]["get"]["operationId"] == "health-get_health"
    assert "ErrorResponse" in schema["components"]["schemas"]


def test_export_openapi_writes_stable_json(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "openapi.json"

    main(["export-openapi", "--output", str(output)])
    first = output.read_bytes()
    main(["export-openapi", "--output", str(output)])

    assert output.read_bytes() == first
    assert first.endswith(b"\n")
    assert b"\r\n" not in first
    assert json.loads(first)["openapi"].startswith("3.")
