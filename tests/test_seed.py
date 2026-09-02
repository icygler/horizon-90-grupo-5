from horizon90.seed import CURATED_EVIDENCE, FIXED_STRATEGIES


def test_seed_has_enough_semantic_evidence():
    assert len(CURATED_EVIDENCE) >= 8
    assert all(item.text and item.source_label for item in CURATED_EVIDENCE)


def test_seed_defines_exactly_three_strategies():
    assert [strategy.id for strategy in FIXED_STRATEGIES] == [
        "PROTEGER_CONEXOES",
        "PROTEGER_PONTUALIDADE",
        "PRIORIZAR_ATENDIMENTO",
    ]

