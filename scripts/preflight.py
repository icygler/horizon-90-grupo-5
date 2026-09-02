"""Check each Horizon 90 cloud dependency independently without exposing secrets."""

from __future__ import annotations

import json
import sys
from typing import Any

from horizon90.bedrock import BedrockClient
from horizon90.config import Settings
from horizon90.storage import ReplayStorage
from horizon90.tidb import TiDBRepository


def run_preflight(settings: Settings | object, tidb: Any = None, bedrock: Any = None, storage: Any = None) -> dict[str, str]:
    result: dict[str, str] = {}
    repository = tidb or TiDBRepository(settings)
    try:
        repository.ping()
        result["tidb"] = "ok"
    except Exception:
        result["tidb"] = "failed"
    try:
        matches = repository.find_evidence("redução de capacidade", 1)
        result["vector"] = "ok" if matches else "failed"
    except Exception:
        result["vector"] = "failed"
    try:
        client = bedrock or BedrockClient.from_env()
        client.invoke_json('{"check":"ping"}')
        result["bedrock"] = "ok"
    except Exception:
        result["bedrock"] = "failed"
    try:
        archive = (storage or ReplayStorage.from_settings(settings)).write_json("preflight", {"check": "ok"})
        result["s3"] = "ok" if archive.status == "archived" else "failed"
    except Exception:
        result["s3"] = "failed"
    return result


def main() -> int:
    result = run_preflight(Settings.from_env())
    print(json.dumps(result, ensure_ascii=False))
    return 0 if all(value == "ok" for value in result.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
