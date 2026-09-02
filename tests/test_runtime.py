from horizon90 import main


def test_default_service_keeps_openai_available_when_tidb_configuration_is_missing(monkeypatch):
    live_llm = object()
    monkeypatch.setattr(main.Settings, "from_env", lambda: (_ for _ in ()).throw(ValueError("TiDB ausente")))
    monkeypatch.setattr(main.OpenAIClient, "from_env", lambda: live_llm)

    service = main.default_service()

    assert service.llm is live_llm
    assert isinstance(service.repository, main.UnavailableRepository)
