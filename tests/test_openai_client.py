import json

from horizon90.openai_client import LUNA_ID, OpenAIClient


class FakeResponses:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return type("Response", (), {"output_text": json.dumps({"likely_reaction": "Confirmar capacidade.", "objection": "É simulado.", "pressure_signal": "Tempo.", "validation_question": "Qual é a capacidade?"})})()


class FakeOpenAI:
    def __init__(self):
        self.responses = FakeResponses()


def test_openai_client_uses_luna_low_reasoning_and_strict_actor_schema():
    fake = FakeOpenAI()
    payload = OpenAIClient(fake).invoke_json("CENARIO_REACAO\nTeste")

    assert payload["likely_reaction"] == "Confirmar capacidade."
    assert fake.responses.kwargs["model"] == LUNA_ID
    assert fake.responses.kwargs["reasoning"] == {"effort": "low"}
    assert fake.responses.kwargs["text"]["format"]["name"] == "actor_reaction"
    assert fake.responses.kwargs["text"]["format"]["strict"] is True
    assert fake.responses.kwargs["store"] is False
