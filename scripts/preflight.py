"""Check each Horizon 90 local demo dependency independently without exposing secrets."""

from __future__ import annotations

import json
import sys
from typing import Any

from horizon90.config import Settings
from horizon90.openai_client import OpenAIClient
from horizon90.storage import LocalReplayStorage
from horizon90.tidb import TiDBRepository


def run_preflight(settings: Settings | object, tidb: Any = None, llm: Any = None, storage: Any = None) -> dict[str, str]:
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
        client = llm or OpenAIClient.from_env()
        client.invoke_json('{"check":"ping"}')
        result["llm"] = "ok"
    except Exception:
        result["llm"] = "failed"
    try:
        archive = (storage or LocalReplayStorage.default()).write_json("preflight", {"check": "ok"})
        result["archive"] = "ok" if archive.status == "archived" else "failed"
    except Exception:
        result["archive"] = "failed"
    return result


def main() -> int:
    result = run_preflight(Settings.from_env())
    print(json.dumps(result, ensure_ascii=False))
    return 0 if all(value == "ok" for value in result.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
