"""Import the supplied airportdb SQL dump without logging source records.

The TiDB Cloud UI requires cross-account S3 IAM access for its managed importer.
This utility is the approved direct-TLS fallback: it runs the event-provided dump
against a TiDB Cloud connection supplied through environment variables.
"""

from __future__ import annotations

import gzip
import os
import re
from pathlib import Path

import pymysql
from dotenv import load_dotenv


DUMP_PATH = Path("tmp/data/hackathon_airportdb.sql.gz")


def split_statements(sql: str) -> list[str]:
    """Split MySQL statements while preserving semicolons inside string literals."""
    statements: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False

    for index, char in enumerate(sql):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in {"'", '"', "`"}:
            quote = char
        elif char == ";":
            statement = sql[start : index + 1].strip()
            if statement:
                statements.append(statement)
            start = index + 1

    trailing = sql[start:].strip()
    if trailing:
        statements.append(trailing)
    return statements


def statement_kind(statement: str) -> str:
    normalized = re.sub(r"^/\\*![0-9]+\\s*", "", statement).strip()
    match = re.match(r"(CREATE TABLE|INSERT INTO|DROP TABLE|CREATE DATABASE|USE)\\s+`?([A-Za-z_]+)?", normalized, re.I)
    if not match:
        return normalized.split(maxsplit=1)[0].upper() if normalized else "EMPTY"
    return " ".join(part for part in match.groups() if part)


def main() -> None:
    load_dotenv()
    required = ("TIDB_HOST", "TIDB_USER", "TIDB_PASSWORD")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise SystemExit(f"Missing required environment keys: {', '.join(missing)}")
    if not DUMP_PATH.exists():
        raise SystemExit(f"Dump not found: {DUMP_PATH}")

    sql = gzip.open(DUMP_PATH, "rt", encoding="utf-8", errors="replace").read()
    statements = split_statements(sql)
    connection = pymysql.connect(
        host=os.environ["TIDB_HOST"],
        port=int(os.getenv("TIDB_PORT", "4000")),
        user=os.environ["TIDB_USER"],
        password=os.environ["TIDB_PASSWORD"],
        database="sys",
        connect_timeout=30,
        read_timeout=600,
        write_timeout=600,
        ssl={"check_hostname": True},
    )

    try:
        with connection.cursor() as cursor:
            for index, statement in enumerate(statements, start=1):
                try:
                    cursor.execute(statement)
                except pymysql.MySQLError as error:
                    raise RuntimeError(
                        f"Import failed at statement {index} ({statement_kind(statement)}): {error.args[0]}"
                    ) from error
                if index % 20 == 0:
                    connection.commit()
                    print(f"Imported {index}/{len(statements)} statements")
        connection.commit()
    finally:
        connection.close()

    print(f"Airportdb import complete: {len(statements)} statements")


if __name__ == "__main__":
    main()
