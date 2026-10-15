import io
import json
from pathlib import Path

import pytest

from bright_smile.agent.kb import KB
from bright_smile.cli import build_openapi_schema, main
from bright_smile.core.security import verify_password


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


def test_hash_password_from_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("correct horse battery\n"))

    main(["hash-password", "--stdin"])

    printed = capsys.readouterr().out.strip()
    assert printed.startswith("$argon2id$")
    assert verify_password("correct horse battery", printed)


def test_hash_password_rejects_short_passwords(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("short\n"))

    with pytest.raises(SystemExit, match="at least 12"):
        main(["hash-password", "--stdin"])


def test_hash_password_ignores_a_piped_byte_order_mark(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(chr(0xFEFF) + "correct horse battery\r\n"))

    main(["hash-password", "--stdin"])

    assert verify_password("correct horse battery", capsys.readouterr().out.strip())


def test_export_kb_matches_the_knowledge_base(tmp_path: Path) -> None:
    output = tmp_path / "kb.json"

    main(["export-kb", "--output", str(output)])

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data == KB.model_dump(mode="json")
    assert data["phone"] == "(301) 555-0148"
