from datetime import datetime

from horizon90.models import Evidence, ExposureSummary, ScenarioContract
from horizon90.service import HorizonService


class FailingRepository:
    def fetch_exposure(self, contract):
        raise ConnectionError("TiDB indisponível")

    def find_evidence(self, query, limit=3):
        raise ConnectionError("TiDB indisponível")


class FakeBedrock:
    def invoke_json(self, prompt, model_id=None):
        return {
            "likely_reaction": "Solicita confirmação.",
            "objection": "É uma simulação.",
            "pressure_signal": "Comunicação imediata.",
            "validation_question": "Qual é a capacidade confirmada?",
        }


class FakeStorage:
    pass


def seeded_contract():
    return ScenarioContract(
        airport_iata="GRU",
        start_at=datetime(2015, 6, 4, 15, 0),
        duration_minutes=90,
        capacity_reduction_pct=30,
        assumptions=["Cenário de simulação; não representa status operacional ao vivo."],
    )


def test_service_labels_vector_fallback_when_repository_fails():
    result = HorizonService(FailingRepository(), FakeBedrock(), FakeStorage()).run(seeded_contract())

    assert result.integration_status.tidb == "fallback"
    assert result.integration_status.vector == "fallback"
    assert result.exposure.source == "seed"
    assert all(isinstance(item, Evidence) for item in result.evidence)
    assert isinstance(result.exposure, ExposureSummary)
