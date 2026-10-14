"""Operational commands: `uv run python -m bright_smile.cli <command>`."""

import argparse
import json
from pathlib import Path
from typing import Any

from bright_smile.core.config import Environment, LogLevel, Settings
from bright_smile.main import create_app

DEFAULT_OPENAPI_PATH = Path(__file__).resolve().parents[3] / "frontend" / "openapi.json"


def build_openapi_schema() -> dict[str, Any]:
    """Return the OpenAPI document without touching the environment or the database.

    Schema generation only needs the route table, so settings are constructed without
    validation and no secrets are required (this runs in CI and on fresh checkouts).
    """
    settings = Settings.model_construct(
        environment=Environment.DEVELOPMENT, log_level=LogLevel.WARNING
    )
    return create_app(settings).openapi()


def export_openapi(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build_openapi_schema(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="bright_smile.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    export = commands.add_parser("export-openapi", help="write the OpenAPI schema for the frontend")
    export.add_argument("--output", type=Path, default=DEFAULT_OPENAPI_PATH)

    args = parser.parse_args(argv)
    if args.command == "export-openapi":
        export_openapi(args.output)


if __name__ == "__main__":
    main()
