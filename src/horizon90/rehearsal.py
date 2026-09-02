"""One-round, four-role airport rehearsal inspired by MiroFish."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any
from uuid import uuid4

from horizon90.bedrock import HAIKU_ID, SONNET_ID
from horizon90.models import AgentReaction, DecisionPack, Evidence, ExposureSummary, ScenarioContract
from horizon90.seed import ACTORS, FIXED_STRATEGIES, ActorDefinition


def run_rehearsal(
    contract: ScenarioContract,
    exposure: ExposureSummary,
    evidence: list[Evidence],
    bedrock: Any,
) -> list[AgentReaction]:
    """Run exactly one independent reaction for each fixed stakeholder role."""
    with ThreadPoolExecutor(max_workers=len(ACTORS)) as pool:
        futures = [pool.submit(_run_actor, actor, contract, exposure, evidence, bedrock) for actor in ACTORS]
        return [future.result(timeout=20) for future in futures]


def build_decision_pack(
    contract: ScenarioContract,
    exposure: ExposureSummary,
    evidence: list[Evidence],
    reactions: list[AgentReaction],
    selected_strategy_id: str,
    bedrock: Any,
) -> DecisionPack:
    """Generate a final, reviewable recommendation only after strategy selection."""
    selected = next((item for item in FIXED_STRATEGIES if item.id == selected_strategy_id), None)
    if selected is None:
        raise ValueError("Estratégia selecionada inválida.")
    prompt = _decision_prompt(contract, exposure, evidence, reactions, selected_strategy_id)
    decision_id = str(uuid4())
    try:
        payload = bedrock.invoke_json(prompt, model_id=SONNET_ID)
        return DecisionPack(
            decision_id=decision_id,
            selected_strategy_id=selected_strategy_id,
            recommended_action=str(payload["recommended_action"]),
            tradeoffs=[str(item) for item in payload["tradeoffs"]],
            evidence_ids=[int(item) for item in payload["evidence_ids"]],
            assumptions=[str(item) for item in payload["assumptions"]],
            human_validation_questions=[str(item) for item in payload["human_validation_questions"]],
        )
    except Exception:
        return DecisionPack(
            decision_id=decision_id,
            selected_strategy_id=selected_strategy_id,
            recommended_action="Validar a estratégia selecionada com a equipe humana antes de qualquer ação.",
            tradeoffs=[selected.tradeoff, "O cenário e a exposição permanecem simulados."],
            evidence_ids=[item.evidence_id for item in evidence if item.evidence_id is not None],
            assumptions=contract.assumptions,
            human_validation_questions=[item.validation_question for item in reactions],
        )


def _run_actor(
    actor: ActorDefinition,
    contract: ScenarioContract,
    exposure: ExposureSummary,
    evidence: list[Evidence],
    bedrock: Any,
) -> AgentReaction:
    prompt = _actor_prompt(actor, contract, exposure, evidence)
    try:
        payload = bedrock.invoke_json(prompt, model_id=HAIKU_ID)
        return AgentReaction(
            actor_id=actor.actor_id,
            actor_label=actor.label,
            round_number=1,
            likely_reaction=str(payload["likely_reaction"]),
            objection=str(payload["objection"]),
            pressure_signal=str(payload["pressure_signal"]),
            validation_question=str(payload["validation_question"]),
            availability="real",
        )
    except Exception:
        return AgentReaction(
            actor_id=actor.actor_id,
            actor_label=actor.label,
            round_number=1,
            likely_reaction="Resposta indisponível para esta rodada.",
            objection="A reação requer validação humana.",
            pressure_signal="Integração de IA indisponível.",
            validation_question="Qual informação operacional precisa ser confirmada?",
            availability="unavailable",
        )


def _actor_prompt(
    actor: ActorDefinition,
    contract: ScenarioContract,
    exposure: ExposureSummary,
    evidence: list[Evidence],
) -> str:
    evidence_text = "\n".join(f"- [{item.evidence_id}] {item.content}" for item in evidence)
    return f"""CENARIO_REACAO
Você representa {actor.label}. Sua preocupação é: {actor.concern}.
Este é um exercício de simulação no aeroporto {contract.airport_iata}, iniciado em
{contract.start_at.isoformat()}, com redução hipotética de {contract.capacity_reduction_pct}%
por {contract.duration_minutes} minutos. Exposição agregada: {exposure.affected_flights}
voos, {exposure.affected_bookings} reservas e capacidade agregada {exposure.affected_capacity}.
Evidências permitidas:\n{evidence_text}

Devolva somente JSON com likely_reaction, objection, pressure_signal e validation_question.
Não afirme cancelamento, atraso ou remarcação reais; não inclua dados pessoais.
"""


def _decision_prompt(
    contract: ScenarioContract,
    exposure: ExposureSummary,
    evidence: list[Evidence],
    reactions: list[AgentReaction],
    selected_strategy_id: str,
) -> str:
    evidence_text = ", ".join(str(item.evidence_id) for item in evidence if item.evidence_id is not None)
    reaction_text = "\n".join(f"- {item.actor_label}: {item.likely_reaction}" for item in reactions)
    return f"""PACOTE_DECISAO
Crie um pacote de decisão para o cenário SIMULADO em {contract.airport_iata}.
Estratégia selecionada: {selected_strategy_id}. Exposição agregada: {exposure.model_dump()}.
IDs de evidência disponíveis: {evidence_text}.
Reações da rodada única:\n{reaction_text}

Devolva somente JSON com recommended_action, tradeoffs, evidence_ids, assumptions e
human_validation_questions. Não afirme que um voo foi realmente cancelado, atrasado ou
remarcado. Exija validação humana antes de qualquer ação.
"""
