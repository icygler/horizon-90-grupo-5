"""Safe application configuration loaded from the environment."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    tidb_host: str
    tidb_port: int
    tidb_user: str
    tidb_password: str
    tidb_database: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        required = ("TIDB_HOST", "TIDB_USER", "TIDB_PASSWORD", "TIDB_DATABASE")
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise ValueError(f"Variáveis ausentes: {', '.join(missing)}")
        return cls(
            tidb_host=os.environ["TIDB_HOST"],
            tidb_port=int(os.getenv("TIDB_PORT", "4000")),
            tidb_user=os.environ["TIDB_USER"],
            tidb_password=os.environ["TIDB_PASSWORD"],
            tidb_database=os.environ["TIDB_DATABASE"],
        )
