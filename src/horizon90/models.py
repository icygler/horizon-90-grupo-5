"""Validated contracts shared by the Horizon 90 application layers."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ScenarioContract(BaseModel):
    airport_iata: str
    start_at: datetime
    duration_minutes: int
    capacity_reduction_pct: int
    assumptions: list[str]
    mode_label: Literal["simulated"] = "simulated"


class ScenarioInput(BaseModel):
    airport_iata: str = Field(pattern=r"^[A-Z]{3}$")
    start_at: datetime
    duration_minutes: int = Field(ge=30, le=180)
    capacity_reduction_pct: int = Field(ge=10, le=80)
    confirmed: bool
    description: str | None = Field(default=None, max_length=600)

    def to_contract(self) -> ScenarioContract:
        if not self.confirmed:
            raise ValueError("O contrato do cenário precisa ser confirmado.")
        return ScenarioContract(
            airport_iata=self.airport_iata,
            start_at=self.start_at,
            duration_minutes=self.duration_minutes,
            capacity_reduction_pct=self.capacity_reduction_pct,
            assumptions=["Cenário de simulação; não representa status operacional ao vivo."],
        )


class Evidence(BaseModel):
    evidence_id: int | None = None
    source_label: str
    source_type: str
    content: str
    distance: float | None = None


class ExposureSummary(BaseModel):
    airport_iata: str
    affected_flights: int
    affected_bookings: int
    affected_capacity: int
    source: Literal["tidb", "seed"]


class Strategy(BaseModel):
    id: Literal["PROTEGER_CONEXOES", "PROTEGER_PONTUALIDADE", "PRIORIZAR_ATENDIMENTO"]
    title: str
    rationale: str
    tradeoff: str


class AgentReaction(BaseModel):
    actor_id: str
    actor_label: str
    round_number: Literal[1]
    likely_reaction: str
    objection: str
    pressure_signal: str
    validation_question: str
    availability: Literal["real", "unavailable"]


class IntegrationStatus(BaseModel):
    tidb: Literal["real", "fallback", "unavailable"]
    vector: Literal["real", "fallback", "unavailable"]
    llm: Literal["real", "fallback", "unavailable"]
    archive: Literal["real", "fallback", "unavailable"]


class OperationalAction(BaseModel):
    time_window: Literal["agora", "15_min", "30_min", "fim_da_janela"]
    owner: str
    action: str
    success_signal: str


class DecisionPack(BaseModel):
    decision_id: str
    selected_strategy_id: str
    recommended_action: str
    tradeoffs: list[str]
    evidence_ids: list[int]
    assumptions: list[str]
    human_validation_questions: list[str]
    action_plan: list[OperationalAction] = Field(default_factory=list)
    impact_watch: list[str] = Field(default_factory=list)
    next_review_minutes: int = Field(default=15, ge=5, le=60)
    archive_status: Literal["archived", "not_archived", "not_requested"] = "not_requested"
    archive_key: str | None = None


class ArchiveResult(BaseModel):
    status: Literal["archived", "not_archived"]
    archive_key: str | None = None
    message: str | None = None


class RunResult(BaseModel):
    run_id: str
    contract: ScenarioContract
    exposure: ExposureSummary
    evidence: list[Evidence]
    strategies: list[Strategy]
    reactions: list[AgentReaction]
    integration_status: IntegrationStatus
