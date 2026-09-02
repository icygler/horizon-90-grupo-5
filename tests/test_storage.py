from horizon90.models import DecisionPack
from horizon90.storage import ReplayStorage


class FakeS3:
    def __init__(self):
        self.key = ""
        self.payload = ""

    def put_object(self, **kwargs):
        self.key = kwargs["Key"]
        self.payload = kwargs["Body"]


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


def test_storage_uses_only_group_five_prefix():
    client = FakeS3()
    result = ReplayStorage(client, "bucket", "latam-hackathon-005").write(decision_pack())

    assert result.status == "archived"
    assert client.key == "latam-hackathon-005/replays/demo-001.json"


def test_storage_rejects_another_team_prefix():
    try:
        ReplayStorage(FakeS3(), "bucket", "latam-hackathon-004")
    except ValueError as error:
        assert "Grupo 5" in str(error)
    else:
        raise AssertionError("O prefixo de outro time deve ser rejeitado.")
