"""One-round, four-role airport rehearsal inspired by MiroFish."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any
from uuid import uuid4

from horizon90.models import AgentReaction, DecisionPack, Evidence, ExposureSummary, OperationalAction, ScenarioContract
from horizon90.openai_client import LUNA_ID
from horizon90.seed import ACTORS, FIXED_STRATEGIES, ActorDefinition


def run_rehearsal(
    contract: ScenarioContract,
    exposure: ExposureSummary,
    evidence: list[Evidence],
    llm: Any,
) -> list[AgentReaction]:
    """Run exactly one independent reaction for each fixed stakeholder role."""
    with ThreadPoolExecutor(max_workers=len(ACTORS)) as pool:
        futures = [pool.submit(_run_actor, actor, contract, exposure, evidence, llm) for actor in ACTORS]
        return [future.result(timeout=20) for future in futures]


def build_decision_pack(
    contract: ScenarioContract,
    exposure: ExposureSummary,
    evidence: list[Evidence],
    reactions: list[AgentReaction],
    selected_strategy_id: str,
    llm: Any,
) -> DecisionPack:
    """Generate a final, reviewable recommendation only after strategy selection."""
    selected = next((item for item in FIXED_STRATEGIES if item.id == selected_strategy_id), None)
    if selected is None:
        raise ValueError("Estratégia selecionada inválida.")
    prompt = _decision_prompt(contract, exposure, evidence, reactions, selected_strategy_id)
    decision_id = str(uuid4())
    try:
        payload = llm.invoke_json(prompt, model_id=LUNA_ID)
        return DecisionPack(
            decision_id=decision_id,
            selected_strategy_id=selected_strategy_id,
            recommended_action=str(payload["recommended_action"]),
            tradeoffs=[str(item) for item in payload["tradeoffs"]],
            evidence_ids=[int(item) for item in payload["evidence_ids"]],
            assumptions=[str(item) for item in payload["assumptions"]],
            human_validation_questions=[str(item) for item in payload["human_validation_questions"]],
            action_plan=[OperationalAction.model_validate(item) for item in payload["action_plan"]],
            impact_watch=[str(item) for item in payload["impact_watch"]],
            next_review_minutes=int(payload["next_review_minutes"]),
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
            action_plan=_fallback_action_plan(),
            impact_watch=["conexões", "pontualidade", "atendimento"],
            next_review_minutes=15,
        )


def _run_actor(
    actor: ActorDefinition,
    contract: ScenarioContract,
    exposure: ExposureSummary,
    evidence: list[Evidence],
    llm: Any,
) -> AgentReaction:
    prompt = _actor_prompt(actor, contract, exposure, evidence)
    try:
        payload = llm.invoke_json(prompt, model_id=LUNA_ID)
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

 Devolva somente JSON com recommended_action, tradeoffs, evidence_ids, assumptions,
 human_validation_questions, action_plan, impact_watch e next_review_minutes.
 action_plan deve ter até quatro itens, um para cada time_window: agora, 15_min, 30_min
 e fim_da_janela. Cada item deve indicar owner, ação sugerida e signal de sucesso.
 Não afirme que um voo foi realmente cancelado, atrasado ou remarcado. Exija validação
 humana antes de qualquer ação.
"""


def _fallback_action_plan() -> list[OperationalAction]:
    return [
        OperationalAction(
            time_window="agora",
            owner="Gestão aeroportuária",
            action="Confirmar a capacidade disponível e abrir a coordenação entre aeroporto, companhia e atendimento.",
            success_signal="Capacidade, responsáveis e canal de coordenação confirmados.",
        ),
        OperationalAction(
            time_window="15_min",
            owner="Operações da companhia",
            action="Validar a estratégia selecionada contra as conexões e a malha expostas.",
            success_signal="Prioridades revisadas pela operação da companhia.",
        ),
        OperationalAction(
            time_window="30_min",
            owner="Atendimento ao passageiro",
            action="Preparar comunicação e contingência somente após a validação humana.",
            success_signal="Mensagem e canais de atendimento prontos para aprovação.",
        ),
        OperationalAction(
            time_window="fim_da_janela",
            owner="Gestão aeroportuária",
            action="Reavaliar a exposição e decidir se a coordenação pode ser encerrada ou escalada.",
            success_signal="Registro de reavaliação concluído pela equipe humana.",
        ),
    ]
