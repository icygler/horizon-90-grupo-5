"""End-to-end orchestration that makes dependency state visible."""

from __future__ import annotations

from uuid import uuid4
from typing import Any

from horizon90.models import Evidence, ExposureSummary, IntegrationStatus, RunResult, ScenarioContract
from horizon90.rehearsal import build_decision_pack, run_rehearsal
from horizon90.seed import CURATED_EVIDENCE, FIXED_STRATEGIES


class HorizonService:
    def __init__(self, repository: Any, llm: Any, storage: Any):
        self.repository = repository
        self.llm = llm
        self.storage = storage
        self._runs: dict[str, RunResult] = {}

    def run(self, contract: ScenarioContract) -> RunResult:
        status = IntegrationStatus(tidb="real", vector="real", llm="real", s3="unavailable")
        try:
            exposure = self.repository.fetch_exposure(contract)
            evidence = self.repository.find_evidence(self._evidence_query(contract), limit=3)
        except Exception:
            exposure = ExposureSummary(
                airport_iata=contract.airport_iata,
                affected_flights=3,
                affected_bookings=180,
                affected_capacity=420,
                source="seed",
            )
            evidence = [
                Evidence(evidence_id=index, source_label=item.source_label, source_type=item.source_type, content=item.text)
                for index, item in enumerate(CURATED_EVIDENCE[:3], start=1)
            ]
            status = status.model_copy(update={"tidb": "fallback", "vector": "fallback"})

        reactions = run_rehearsal(contract, exposure, evidence, self.llm)
        if any(reaction.availability == "unavailable" for reaction in reactions):
            status = status.model_copy(update={"llm": "unavailable"})
        result = RunResult(
            run_id=str(uuid4()),
            contract=contract,
            exposure=exposure,
            evidence=evidence,
            strategies=FIXED_STRATEGIES,
            reactions=reactions,
            integration_status=status,
        )
        self._runs[result.run_id] = result
        return result

    def select_strategy(self, run_id: str, strategy_id: str):
        run = self._runs.get(run_id)
        if run is None:
            raise ValueError("Execução não encontrada.")
        pack = build_decision_pack(
            run.contract,
            run.exposure,
            run.evidence,
            run.reactions,
            strategy_id,
            self.llm,
        )
        archive = self.storage.write(pack)
        s3_status = "real" if archive.status == "archived" else "unavailable"
        self._runs[run_id] = run.model_copy(
            update={"integration_status": run.integration_status.model_copy(update={"s3": s3_status})}
        )
        return pack.model_copy(update={"archive_status": archive.status, "archive_key": archive.s3_key})

    @staticmethod
    def _evidence_query(contract: ScenarioContract) -> str:
        return (
            f"redução de {contract.capacity_reduction_pct}% de capacidade em "
            f"{contract.airport_iata} por {contract.duration_minutes} minutos"
        )
