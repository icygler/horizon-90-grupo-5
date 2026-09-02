from datetime import datetime

from fastapi.testclient import TestClient

from horizon90.main import create_app
from horizon90.models import (
    AgentReaction,
    Evidence,
    ExposureSummary,
    IntegrationStatus,
    RunResult,
    ScenarioContract,
    Strategy,
)


class FakeService:
    def run(self, contract):
        return RunResult(
            run_id="run-001",
            contract=contract,
            exposure=ExposureSummary(
                airport_iata="GRU", affected_flights=3, affected_bookings=180, affected_capacity=420, source="seed"
            ),
            evidence=[Evidence(evidence_id=1, source_label="Política", source_type="policy", content="Comunicar cedo.")],
            strategies=[
                Strategy(
                    id="PROTEGER_CONEXOES",
                    title="Proteger conexões",
                    rationale="Priorizar conexões.",
                    tradeoff="Pressão no atendimento.",
                )
            ],
            reactions=[
                AgentReaction(
                    actor_id="airline_ops",
                    actor_label="Operações da companhia",
                    round_number=1,
                    likely_reaction="Confirmar capacidade.",
                    objection="Simulação.",
                    pressure_signal="Tempo.",
                    validation_question="Qual capacidade?",
                    availability="real",
                )
            ],
            integration_status=IntegrationStatus(tidb="fallback", vector="fallback", bedrock="real", s3="unavailable"),
        )


def test_seed_endpoint_returns_confirmed_gru_scenario():
    client = TestClient(create_app(FakeService()))
    response = client.get("/api/seed")

    assert response.status_code == 200
    assert response.json()["airport_iata"] == "GRU"
    assert response.json()["confirmed"] is True


def test_run_endpoint_requires_complete_confirmed_contract():
    client = TestClient(create_app(FakeService()))
    response = client.post("/api/runs", json={"airport_iata": "GRU", "confirmed": False})

    assert response.status_code == 422


def test_run_endpoint_returns_status_without_personal_data():
    client = TestClient(create_app(FakeService()))
    response = client.post(
        "/api/runs",
        json={
            "airport_iata": "GRU",
            "start_at": datetime(2015, 6, 4, 15, 0).isoformat(),
            "duration_minutes": 90,
            "capacity_reduction_pct": 30,
            "confirmed": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["integration_status"]["tidb"] == "fallback"
    assert "passport" not in response.text.lower()
