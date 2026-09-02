from datetime import datetime

from horizon90.openai_client import LUNA_ID
from horizon90.models import Evidence, ExposureSummary, ScenarioContract
from horizon90.rehearsal import build_decision_pack, run_rehearsal


class FakeBedrock:
    def __init__(self):
        self.prompts: list[str] = []
        self.model_ids: list[str | None] = []

    def invoke_json(self, prompt, model_id=None):
        self.prompts.append(prompt)
        self.model_ids.append(model_id)
        if "PACOTE_DECISAO" in prompt:
            return {
                "recommended_action": "Validar a estratégia selecionada com a equipe humana.",
                "tradeoffs": ["O cenário continua simulado."],
                "evidence_ids": [1],
                "assumptions": ["Sem status operacional ao vivo."],
                "human_validation_questions": ["Qual é a capacidade confirmada?"],
                "action_plan": [
                    {
                        "time_window": "agora",
                        "owner": "Gestão aeroportuária",
                        "action": "Confirmar capacidade disponível e abrir coordenação conjunta.",
                        "success_signal": "Capacidade e canal de coordenação confirmados.",
                    }
                ],
                "impact_watch": ["conexões", "pontualidade", "atendimento"],
                "next_review_minutes": 15,
            }
        return {
            "likely_reaction": "Solicita confirmação antes de agir.",
            "objection": "A exposição ainda é simulada.",
            "pressure_signal": "A comunicação precisa ser imediata.",
            "validation_question": "Qual é a capacidade confirmada?",
        }


class FailingBedrock:
    def invoke_json(self, prompt, model_id=None):
        raise ConnectionError("Bedrock indisponível")


def seeded_contract():
    return ScenarioContract(
        airport_iata="GRU",
        start_at=datetime(2015, 6, 4, 15, 0),
        duration_minutes=90,
        capacity_reduction_pct=30,
        assumptions=["Cenário de simulação; não representa status operacional ao vivo."],
    )


def seeded_exposure():
    return ExposureSummary(
        airport_iata="GRU",
        affected_flights=3,
        affected_bookings=180,
        affected_capacity=420,
        source="seed",
    )


def seeded_evidence():
    return [Evidence(evidence_id=1, source_label="Política", source_type="policy", content="Comunicar cedo.")]


def test_rehearsal_returns_one_reaction_per_fixed_actor():
    reactions = run_rehearsal(seeded_contract(), seeded_exposure(), seeded_evidence(), FakeBedrock())

    assert [reaction.actor_id for reaction in reactions] == [
        "airline_ops",
        "airport_duty_manager",
        "short_connection_passenger",
        "customer_service",
    ]
    assert all(reaction.round_number == 1 for reaction in reactions)


def test_rehearsal_never_sends_personal_data_in_prompt():
    bedrock = FakeBedrock()
    run_rehearsal(seeded_contract(), seeded_exposure(), seeded_evidence(), bedrock)

    prompt_text = "\n".join(bedrock.prompts).lower()
    assert "passport" not in prompt_text
    assert "emailaddress" not in prompt_text


def test_rehearsal_labels_unavailable_actor_responses():
    reactions = run_rehearsal(seeded_contract(), seeded_exposure(), seeded_evidence(), FailingBedrock())

    assert all(reaction.availability == "unavailable" for reaction in reactions)


def test_decision_pack_uses_luna_only_after_strategy_selection():
    bedrock = FakeBedrock()
    reactions = run_rehearsal(seeded_contract(), seeded_exposure(), seeded_evidence(), bedrock)

    pack = build_decision_pack(
        seeded_contract(),
        seeded_exposure(),
        seeded_evidence(),
        reactions,
        "PROTEGER_CONEXOES",
        bedrock,
    )

    assert pack.selected_strategy_id == "PROTEGER_CONEXOES"
    assert bedrock.model_ids[-1] == LUNA_ID


def test_decision_pack_returns_timed_actions_and_a_review_gate():
    pack = build_decision_pack(
        seeded_contract(),
        seeded_exposure(),
        seeded_evidence(),
        run_rehearsal(seeded_contract(), seeded_exposure(), seeded_evidence(), FakeBedrock()),
        "PROTEGER_CONEXOES",
        FakeBedrock(),
    )

    assert pack.next_review_minutes == 15
    assert pack.action_plan[0].time_window == "agora"
    assert "conexões" in pack.impact_watch
