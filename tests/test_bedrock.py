import json
from datetime import datetime

from horizon90.bedrock import BedrockClient
from horizon90.models import ScenarioContract


class FakeBody:
    def __init__(self, text):
        self.text = text

    def read(self):
        return json.dumps({"content": [{"text": self.text}]}).encode()


class FakeRuntime:
    def __init__(self, text):
        self.text = text

    def invoke_model(self, **kwargs):
        self.last_body = json.loads(kwargs["body"])["messages"][0]["content"]
        return {"body": FakeBody(self.text)}


def seeded_contract() -> ScenarioContract:
    return ScenarioContract(
        airport_iata="GRU",
        start_at=datetime(2015, 6, 4, 15, 0),
        duration_minutes=90,
        capacity_reduction_pct=30,
        assumptions=["Cenário de simulação; não representa status operacional ao vivo."],
    )


def test_parse_scenario_uses_valid_json_response():
    runtime = FakeRuntime('{"airport_iata":"GRU","duration_minutes":90,"capacity_reduction_pct":30}')
    result = BedrockClient(runtime).parse_scenario("GRU perde 30%", seeded_contract())

    assert result.airport_iata == "GRU"
    assert result.duration_minutes == 90


def test_parse_scenario_returns_seed_when_json_is_invalid():
    seed = seeded_contract()
    result = BedrockClient(FakeRuntime("não é JSON")).parse_scenario("texto", seed)

    assert result == seed


def test_parser_prompt_prohibits_inventing_missing_values():
    runtime = FakeRuntime('{"airport_iata":"GRU"}')
    BedrockClient(runtime).parse_scenario("texto", seeded_contract())

    assert "Não invente valores ausentes" in runtime.last_body
