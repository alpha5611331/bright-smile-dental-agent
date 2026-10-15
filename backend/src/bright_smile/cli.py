"""Operational commands: `uv run python -m bright_smile.cli <command>`."""

import argparse
import getpass
import json
import sys
from pathlib import Path
from typing import Any

from bright_smile.core.config import Environment, LogLevel, Settings
from bright_smile.core.security import hash_password
from bright_smile.main import create_app

MIN_PASSWORD_LENGTH = 12

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


def read_new_password(*, from_stdin: bool) -> str:
    """Read the staff password: one line from stdin, or an interactive prompt typed twice."""
    if from_stdin:
        # PowerShell prepends a UTF-8 BOM when piping into native programs; it is never part of
        # the password.
        password = sys.stdin.readline().rstrip("\r\n").removeprefix("﻿")
    else:
        password = getpass.getpass("New staff password: ")
        if getpass.getpass("Repeat password: ") != password:
            raise SystemExit("Passwords do not match.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise SystemExit(f"Use at least {MIN_PASSWORD_LENGTH} characters.")
    return password


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="bright_smile.cli", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    export = commands.add_parser("export-openapi", help="write the OpenAPI schema for the frontend")
    export.add_argument("--output", type=Path, default=DEFAULT_OPENAPI_PATH)

    hash_cmd = commands.add_parser(
        "hash-password", help="print an Argon2 hash for STAFF_PASSWORD_HASH"
    )
    hash_cmd.add_argument(
        "--stdin", action="store_true", help="read the password from stdin (for scripts)"
    )

    args = parser.parse_args(argv)
    if args.command == "export-openapi":
        export_openapi(args.output)
    elif args.command == "hash-password":
        print(hash_password(read_new_password(from_stdin=args.stdin)))  # noqa: T201  # CLI output


if __name__ == "__main__":
    main()
