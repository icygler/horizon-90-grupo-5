"""OpenAI Responses adapter for structured Horizon 90 deliberations."""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI


LUNA_ID = "gpt-5.6-luna"

ACTOR_SCHEMA = {
    "type": "object",
    "properties": {
        "likely_reaction": {"type": "string"},
        "objection": {"type": "string"},
        "pressure_signal": {"type": "string"},
        "validation_question": {"type": "string"},
    },
    "required": ["likely_reaction", "objection", "pressure_signal", "validation_question"],
    "additionalProperties": False,
}

DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "recommended_action": {"type": "string"},
        "tradeoffs": {"type": "array", "items": {"type": "string"}},
        "evidence_ids": {"type": "array", "items": {"type": "integer"}},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "human_validation_questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["recommended_action", "tradeoffs", "evidence_ids", "assumptions", "human_validation_questions"],
    "additionalProperties": False,
}


class OpenAIClient:
    """Calls GPT-5.6 Luna without sending personal airport records."""

    def __init__(self, client: Any):
        self.client = client

    @classmethod
    def from_env(cls) -> "OpenAIClient":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Variável ausente: OPENAI_API_KEY")
        return cls(OpenAI(api_key=api_key))

    def invoke_json(self, prompt: str, model_id: str | None = None) -> dict[str, object]:
        schema_name, schema = self._schema_for(prompt)
        response = self.client.responses.create(
            model=model_id or LUNA_ID,
            input=prompt,
            reasoning={"effort": "low"},
            max_output_tokens=700,
            store=False,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                }
            },
        )
        return json.loads(response.output_text)

    @staticmethod
    def _schema_for(prompt: str) -> tuple[str, dict[str, object]]:
        if prompt.startswith("PACOTE_DECISAO"):
            return "decision_pack", DECISION_SCHEMA
        return "actor_reaction", ACTOR_SCHEMA
