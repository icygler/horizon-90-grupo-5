from horizon90.models import DecisionPack
from horizon90.storage import LocalReplayStorage


def decision_pack():
    return DecisionPack(
        decision_id="demo-001",
        selected_strategy_id="PROTEGER_CONEXOES",
        recommended_action="Validar com a equipe humana.",
        tradeoffs=["Simulação."],
        evidence_ids=[1],
        assumptions=["Sem status ao vivo."],
        human_validation_questions=["Qual é a capacidade confirmada?"],
    )


def test_local_storage_writes_the_decision_pack_to_the_session_directory(tmp_path):
    result = LocalReplayStorage(tmp_path).write(decision_pack())

    assert result.status == "archived"
    assert result.archive_key == "local:demo-001.json"
    assert (tmp_path / "demo-001.json").exists()


def test_local_storage_writes_a_preflight_record(tmp_path):
    result = LocalReplayStorage(tmp_path).write_json("preflight", {"check": "ok"})

    assert result.status == "archived"
    assert (tmp_path / "preflight.json").exists()
