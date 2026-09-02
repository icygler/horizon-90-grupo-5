from horizon90.models import Evidence
from scripts.preflight import run_preflight


class FakeRepository:
    def ping(self):
        return None

    def find_evidence(self, query, limit=1):
        return [Evidence(evidence_id=1, source_label="Teste", source_type="policy", content="ok")]


class FakeLLM:
    def invoke_json(self, prompt, model_id=None):
        return {"check": "ok"}


class FakeStorage:
    def write_json(self, replay_id, payload):
        return type("Archive", (), {"status": "archived"})()


def test_preflight_reports_each_dependency_without_stopping():
    result = run_preflight(
        object(),
        tidb=FakeRepository(),
        llm=FakeLLM(),
        storage=FakeStorage(),
    )

    assert result == {"tidb": "ok", "vector": "ok", "llm": "ok", "s3": "ok"}
