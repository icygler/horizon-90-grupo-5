"""Small, schema-checked Amazon Bedrock adapter with explicit fallbacks."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import boto3

from horizon90.models import ScenarioContract


HAIKU_ID = "anthropic.claude-3-haiku-20240307-v1:0"
SONNET_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"


def extract_json_object(text: str) -> str:
    """Extract one JSON object from a model response, including fenced output."""
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("A resposta não contém um objeto JSON.")
    return match.group(0)


class BedrockClient:
    def __init__(self, runtime: Any):
        self.runtime = runtime

    @classmethod
    def from_env(cls) -> "BedrockClient":
        if not os.getenv("AWS_BEARER_TOKEN_BEDROCK"):
            raise ValueError("Variável ausente: AWS_BEARER_TOKEN_BEDROCK")
        runtime = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "ap-southeast-1"))
        return cls(runtime)

    def invoke_json(self, prompt: str, model_id: str = HAIKU_ID) -> dict[str, object]:
        response = self.runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(
                {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 700,
                    "messages": [{"role": "user", "content": prompt}],
                }
            ),
        )
        text = json.loads(response["body"].read())["content"][0]["text"]
        return json.loads(extract_json_object(text))

    def parse_scenario(self, description: str, fallback: ScenarioContract) -> ScenarioContract:
        prompt = f"""Extraia um contrato de cenário aeroportuário da descrição abaixo.
Devolva somente um objeto JSON com airport_iata, start_at, duration_minutes,
capacity_reduction_pct e assumptions. Não invente valores ausentes; devolva null
quando não houver base. Este é um cenário simulado, não um status operacional.

Descrição: {description}
"""
        try:
            parsed = self.invoke_json(prompt)
            payload = {
                "airport_iata": parsed.get("airport_iata") or fallback.airport_iata,
                "start_at": parsed.get("start_at") or fallback.start_at,
                "duration_minutes": parsed.get("duration_minutes") or fallback.duration_minutes,
                "capacity_reduction_pct": parsed.get("capacity_reduction_pct") or fallback.capacity_reduction_pct,
                "assumptions": parsed.get("assumptions") or fallback.assumptions,
            }
            return ScenarioContract.model_validate(payload)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return fallback
