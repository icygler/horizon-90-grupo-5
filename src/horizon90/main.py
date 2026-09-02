"""FastAPI entry point for the Horizon 90 single-screen console."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from horizon90.config import Settings
from horizon90.models import ArchiveResult, ScenarioInput
from horizon90.service import HorizonService
from horizon90.storage import LocalReplayStorage
from horizon90.tidb import TiDBRepository
from horizon90.openai_client import OpenAIClient


STATIC_DIR = Path(__file__).with_name("static")
SEED_SCENARIO = {
    "airport_iata": "GRU",
    "start_at": "2015-06-04T15:00:00",
    "duration_minutes": 90,
    "capacity_reduction_pct": 30,
    "confirmed": True,
    "description": "Exercício simulado: GRU perde 30% de capacidade durante 90 minutos.",
}


class DecisionSelection(BaseModel):
    strategy_id: str


class UnavailableRepository:
    def fetch_exposure(self, contract: Any):
        raise ConnectionError("TiDB não configurado")

    def find_evidence(self, query: str, limit: int = 3):
        raise ConnectionError("TiDB não configurado")


class UnavailableLLM:
    def invoke_json(self, prompt: str, model_id: str | None = None):
        raise ConnectionError("LLM não configurado")


class UnavailableStorage:
    def write(self, pack: Any) -> ArchiveResult:
        return ArchiveResult(status="not_archived", message="Registro local indisponível")


def default_service() -> HorizonService:
    storage: Any = LocalReplayStorage.default()
    try:
        settings = Settings.from_env()
    except ValueError:
        return HorizonService(UnavailableRepository(), UnavailableLLM(), storage)

    repository = TiDBRepository(settings)
    try:
        llm: Any = OpenAIClient.from_env()
    except ValueError:
        llm = UnavailableLLM()
    return HorizonService(repository, llm, storage)


def create_app(service: HorizonService | Any | None = None) -> FastAPI:
    app = FastAPI(title="Horizon 90", version="0.1.0")
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.state.service = service or default_service()

    @app.exception_handler(ValueError)
    async def value_error_handler(request, error: ValueError):
        return JSONResponse(status_code=422, content={"status": "invalid", "message": str(error)})

    @app.get("/", include_in_schema=False)
    def pitch() -> FileResponse:
        return FileResponse(STATIC_DIR / "pitch.html")

    @app.get("/console", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/seed")
    def seed() -> dict[str, object]:
        return SEED_SCENARIO

    @app.post("/api/runs")
    def create_run(payload: ScenarioInput):
        try:
            return app.state.service.run(payload.to_contract())
        except ValueError as error:
            raise HTTPException(status_code=422, detail={"status": "invalid", "message": str(error)}) from error
        except Exception:
            raise HTTPException(status_code=503, detail={"status": "unavailable", "message": "Não foi possível iniciar o ensaio."})

    @app.post("/api/runs/{run_id}/decision")
    def create_decision(run_id: str, payload: DecisionSelection):
        try:
            return app.state.service.select_strategy(run_id, payload.strategy_id)
        except ValueError as error:
            raise HTTPException(status_code=422, detail={"status": "invalid", "message": str(error)}) from error
        except Exception:
            raise HTTPException(status_code=503, detail={"status": "unavailable", "message": "Não foi possível gerar o pacote."})

    return app


app = create_app()
