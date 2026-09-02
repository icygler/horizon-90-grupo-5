import pytest

from horizon90 import config
from horizon90.config import Settings


def test_settings_rejects_missing_tidb_host(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.delenv("TIDB_HOST", raising=False)

    with pytest.raises(ValueError, match="TIDB_HOST"):
        Settings.from_env()
