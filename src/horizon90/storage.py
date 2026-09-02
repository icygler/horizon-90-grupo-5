"""Replay archive writer constrained to the Group 5 S3 prefix."""

from __future__ import annotations

import json
from typing import Any

import boto3
from botocore.exceptions import ClientError

from horizon90.config import Settings
from horizon90.models import ArchiveResult, DecisionPack


GROUP_FIVE_PREFIX = "latam-hackathon-005"


class ReplayStorage:
    def __init__(self, client: Any, bucket: str, prefix: str):
        normalized_prefix = prefix.strip("/")
        if normalized_prefix != GROUP_FIVE_PREFIX:
            raise ValueError("O replay só pode usar o prefixo reservado ao Grupo 5.")
        self.client = client
        self.bucket = bucket
        self.prefix = normalized_prefix

    @classmethod
    def from_settings(cls, settings: Settings) -> "ReplayStorage":
        client = boto3.client("s3", region_name="sa-east-1")
        return cls(client, settings.s3_bucket, settings.s3_prefix)

    def write(self, pack: DecisionPack) -> ArchiveResult:
        return self.write_json(pack.decision_id, pack.model_dump())

    def write_json(self, replay_id: str, payload: dict[str, object]) -> ArchiveResult:
        key = f"{self.prefix}/replays/{replay_id}.json"
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                ContentType="application/json",
            )
            return ArchiveResult(status="archived", s3_key=key)
        except ClientError as error:
            return ArchiveResult(status="not_archived", message=error.response["Error"].get("Code", "S3Error"))
        except Exception:
            return ArchiveResult(status="not_archived", message="S3 indisponível")
