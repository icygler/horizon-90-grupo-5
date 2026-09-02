"""Local, per-session decision-pack storage for the demo runtime."""

from __future__ import annotations

import json
from pathlib import Path

from horizon90.models import ArchiveResult, DecisionPack


class LocalReplayStorage:
    """Write reviewable packs locally; no AWS service is implied or required."""

    def __init__(self, directory: Path):
        self.directory = directory

    @classmethod
    def default(cls) -> "LocalReplayStorage":
        project_root = Path(__file__).resolve().parents[2]
        return cls(project_root / "tmp" / "replays")

    def write(self, pack: DecisionPack) -> ArchiveResult:
        return self.write_json(pack.decision_id, pack.model_dump())

    def write_json(self, record_id: str, payload: dict[str, object]) -> ArchiveResult:
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            filename = f"{record_id}.json"
            (self.directory / filename).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
            )
            return ArchiveResult(status="archived", archive_key=f"local:{filename}")
        except OSError:
            return ArchiveResult(status="not_archived", message="Registro local indisponível")
