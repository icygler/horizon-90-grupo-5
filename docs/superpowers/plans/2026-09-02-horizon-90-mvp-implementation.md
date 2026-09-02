# Histórico — plano inicial do Horizon 90

> Este plano contém o desenho exploratório de Bedrock, S3 e EC2, que não foi a entrega final. A implementação avaliada usa execução local, TiDB, TiDB Vector, OpenAI Responses/GPT-5.6 Luna e arquivo local. Consulte [README](../../../README.md), [EVALUATION](../../../EVALUATION.md), [SUBMISSION](../../../SUBMISSION.md) e [`.kiro/specs/horizon-90/`](../../../.kiro/specs/horizon-90/).

# Horizon 90 MVP Implementation Plan (histórico)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lightweight, evidence-backed airport decision rehearsal that runs one seeded scenario through TiDB, vector retrieval, Bedrock, S3, and a public EC2-hosted console.

**Architecture:** One FastAPI process serves a static browser console and JSON API. TiDB Cloud persists scenarios, aggregate exposure, curated semantic evidence, and decision records; Bedrock parses the scenario and performs a four-role, one-round rehearsal; S3 archives a replay JSON. The default path is a real integration path with a clearly labelled local fallback only when a dependency fails.

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, Pydantic v2, PyMySQL, boto3 >= 1.39, TiDB Cloud Starter, TiDB `EMBED_TEXT` vector search, Amazon Bedrock, Amazon S3, vanilla HTML/CSS/JavaScript, pytest.

**Spec:** `docs/superpowers/specs/2026-09-02-horizon-90-airport-digital-rehearsal-design.md`

## Global Constraints

- Use exactly one FastAPI process and static browser assets; no Node runtime is required on the EC2 instance.
- Run Bedrock only in `ap-southeast-1` with the supplied bearer token; use Haiku for extraction and role responses, Sonnet only for the final decision pack.
- Treat `airportdb` as a simulation baseline. Never state that a result is a real-world prediction, rebooking, or live operational state.
- Use only aggregate passenger counts and route facts. Never query, log, prompt, return, or commit passenger or employee PII.
- Persist all application state in TiDB Cloud Starter and use a real `VECTOR(1024)` generated with `EMBED_TEXT` plus a visible semantic query.
- Write S3 objects only under `s3://tidb-latam-hackathon-2026-048364544505/latam-hackathon-005/`.
- Bind the EC2 process to `0.0.0.0` on a port from 8000-8999. Keep `.env` out of Git.
- Label the built-in behavior as `multi-agent rehearsal inspired by MiroFish`; do not claim a MiroFish integration unless an attributed external report is imported.
- Keep user-facing Portuguese concise and label all fallback, simulated, and unavailable states.

---

## File Structure

| Path | Responsibility |
|---|---|
| `src/horizon90/config.py` | Read and validate environment configuration without exposing secrets. |
| `src/horizon90/models.py` | Pydantic request/response and domain models. |
| `src/horizon90/seed.py` | Curated evidence, three fixed strategies, four fixed actor definitions, and local fallback data. |
| `src/horizon90/tidb.py` | TLS database connection, schema initialization, aggregate exposure query, and vector retrieval. |
| `src/horizon90/bedrock.py` | Direct Bedrock runtime calls and strict JSON parsing. |
| `src/horizon90/rehearsal.py` | Concurrent single-round actor rehearsal and final decision-pack synthesis. |
| `src/horizon90/storage.py` | S3 team-prefix replay writer and local failure result. |
| `src/horizon90/service.py` | End-to-end orchestration with explicit integration status. |
| `src/horizon90/main.py` | FastAPI routes, static assets, and health endpoint. |
| `src/horizon90/static/` | Single-screen Portuguese console with status, scenario, strategies, reactions, and decision pack. |
| `sql/schema.sql` | App-specific TiDB tables and vector index. |
| `scripts/preflight.py` | Checks TiDB, vector retrieval, Bedrock, and S3 independently. |
| `.kiro/` | Requirements, design constraints, and acceptance criteria. |
| `SUBMISSION.md` | Evidence paths for each stack claim and demo link placeholder. |
| `tests/` | Fast, isolated unit and API tests with fake integrations. |

### Task 1: Bootstrap the lightweight application contract

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/horizon90/__init__.py`
- Create: `src/horizon90/config.py`
- Create: `src/horizon90/models.py`
- Create: `tests/test_config.py`
- Create: `tests/test_models.py`
- Create: `tests/conftest.py`

**Interfaces:**
- Produces `Settings`, `ScenarioInput`, `ScenarioContract`, `IntegrationStatus`, `ExposureSummary`, `Strategy`, `AgentReaction`, and `DecisionPack` for all later tasks.
- `Settings.from_env() -> Settings` raises `ValueError` naming the missing key but never including secret values.
- `ScenarioInput.to_contract() -> ScenarioContract` validates a confirmed structured scenario.

- [ ] **Step 1: Write the failing configuration and model tests**

```python
from horizon90.config import Settings
from horizon90.models import ScenarioInput


def test_settings_rejects_missing_tidb_host(monkeypatch):
    monkeypatch.delenv("TIDB_HOST", raising=False)
    with pytest.raises(ValueError, match="TIDB_HOST"):
        Settings.from_env()


def test_scenario_requires_confirmation():
    scenario = ScenarioInput(
        airport_iata="GRU", start_at="2015-06-04T15:00:00",
        duration_minutes=90, capacity_reduction_pct=30, confirmed=False,
    )
    with pytest.raises(ValueError, match="confirmado"):
        scenario.to_contract()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_config.py tests/test_models.py -v`

Expected: FAIL because `horizon90` modules do not exist.

- [ ] **Step 3: Create the project files and minimal implementation**

```python
# src/horizon90/config.py
@dataclass(frozen=True)
class Settings:
    tidb_host: str
    tidb_port: int
    tidb_user: str
    tidb_password: str
    tidb_database: str
    aws_region: str
    s3_bucket: str
    s3_prefix: str

    @classmethod
    def from_env(cls) -> "Settings":
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
            aws_region=os.getenv("AWS_REGION", "ap-southeast-1"),
            s3_bucket=os.getenv("S3_BUCKET", "tidb-latam-hackathon-2026-048364544505"),
            s3_prefix=os.getenv("S3_PREFIX", "latam-hackathon-005"),
        )

# src/horizon90/models.py
class ScenarioContract(BaseModel):
    airport_iata: str
    start_at: datetime
    duration_minutes: int
    capacity_reduction_pct: int
    assumptions: list[str]
    mode_label: Literal["simulated"] = "simulated"

class ScenarioInput(BaseModel):
    airport_iata: str = Field(pattern=r"^[A-Z]{3}$")
    start_at: datetime
    duration_minutes: int = Field(ge=30, le=180)
    capacity_reduction_pct: int = Field(ge=10, le=80)
    confirmed: bool
    description: str | None = Field(default=None, max_length=600)

    def to_contract(self) -> "ScenarioContract":
        if not self.confirmed:
            raise ValueError("O contrato do cenário precisa ser confirmado.")
        return ScenarioContract(
            airport_iata=self.airport_iata,
            start_at=self.start_at,
            duration_minutes=self.duration_minutes,
            capacity_reduction_pct=self.capacity_reduction_pct,
            assumptions=["Cenário de simulação; não representa status operacional ao vivo."],
        )

class Evidence(BaseModel):
    evidence_id: int | None = None
    source_label: str
    source_type: str
    content: str
    distance: float | None = None

class ExposureSummary(BaseModel):
    airport_iata: str
    affected_flights: int
    affected_bookings: int
    affected_capacity: int
    source: Literal["tidb", "seed"]

class Strategy(BaseModel):
    id: Literal["PROTEGER_CONEXOES", "PROTEGER_PONTUALIDADE", "PRIORIZAR_ATENDIMENTO"]
    title: str
    rationale: str
    tradeoff: str

class AgentReaction(BaseModel):
    actor_id: str
    actor_label: str
    round_number: Literal[1]
    likely_reaction: str
    objection: str
    pressure_signal: str
    validation_question: str
    availability: Literal["real", "unavailable"]

class IntegrationStatus(BaseModel):
    tidb: Literal["real", "fallback", "unavailable"]
    vector: Literal["real", "fallback", "unavailable"]
    bedrock: Literal["real", "fallback", "unavailable"]
    s3: Literal["real", "fallback", "unavailable"]

class DecisionPack(BaseModel):
    decision_id: str
    selected_strategy_id: str
    recommended_action: str
    tradeoffs: list[str]
    evidence_ids: list[int]
    assumptions: list[str]
    human_validation_questions: list[str]

class ArchiveResult(BaseModel):
    status: Literal["archived", "not_archived"]
    s3_key: str | None = None
    message: str | None = None

class RunResult(BaseModel):
    run_id: str
    contract: ScenarioContract
    exposure: ExposureSummary
    evidence: list[Evidence]
    strategies: list[Strategy]
    reactions: list[AgentReaction]
    integration_status: IntegrationStatus
```

- [ ] **Step 4: Add dependency and environment files**

```text
# requirements.txt
fastapi==0.116.1
uvicorn[standard]==0.35.0
pydantic==2.11.7
pymysql==1.1.1
boto3>=1.39,<2.0
python-dotenv==1.1.1
pytest==8.4.1
httpx==0.28.1
```

```text
# .env.example
AWS_BEARER_TOKEN_BEDROCK=
AWS_REGION=ap-southeast-1
TIDB_HOST=
TIDB_PORT=4000
TIDB_USER=
TIDB_PASSWORD=
TIDB_DATABASE=airportdb
S3_BUCKET=tidb-latam-hackathon-2026-048364544505
S3_PREFIX=latam-hackathon-005
```

```toml
# pyproject.toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

```python
# tests/conftest.py
class FakeRuntime:
    def __init__(self):
        self.text = "{}"

    def invoke_model(self, **kwargs):
        return {"body": FakeBody(self.text)}

class FakeBody:
    def __init__(self, text):
        self.text = text

    def read(self):
        return json.dumps({"content": [{"text": self.text}]}).encode()

class FakeBedrockClient:
    def __init__(self):
        self.prompts = []

    def invoke_json(self, prompt, model_id=None):
        self.prompts.append(prompt)
        return {
            "likely_reaction": "Solicita confirmação antes de agir.",
            "objection": "A exposição ainda é simulada.",
            "pressure_signal": "Comunicação precisa ser imediata.",
            "validation_question": "Qual é a capacidade confirmada?",
        }

class FakeRepository:
    def ping(self):
        return None

    def find_evidence(self, query, limit=3):
        return [Evidence(evidence_id=1, source_label="Política", source_type="policy", content=query)]

class FailingRepository:
    def fetch_exposure(self, contract):
        raise ConnectionError("TiDB indisponível")

    def find_evidence(self, query, limit=3):
        raise ConnectionError("TiDB indisponível")

class FakeStorage:
    def __init__(self):
        self.key = ""

    def write(self, pack):
        self.key = f"latam-hackathon-005/replays/{pack.decision_id}.json"
        return ArchiveResult(status="archived", s3_key=self.key)

    def write_json(self, replay_id, payload):
        self.key = f"latam-hackathon-005/replays/{replay_id}.json"
        return ArchiveResult(status="archived", s3_key=self.key)

@pytest.fixture
def seeded_contract():
    return ScenarioContract(
        airport_iata="GRU", start_at=datetime(2015, 6, 4, 15, 0),
        duration_minutes=90, capacity_reduction_pct=30,
        assumptions=["Cenário de simulação; não representa status operacional ao vivo."],
    )

@pytest.fixture
def fake_bedrock():
    return FakeBedrockClient()

@pytest.fixture
def fake_runtime():
    return FakeRuntime()

@pytest.fixture
def seeded_exposure():
    return ExposureSummary(airport_iata="GRU", affected_flights=3,
                           affected_bookings=180, affected_capacity=420,
                           source="seed")

@pytest.fixture
def seeded_evidence():
    return [Evidence(evidence_id=1, source_label="Política de comunicação",
                     source_type="policy", content="Informar passageiros afetados cedo.")]

@pytest.fixture
def fake_storage():
    return FakeStorage()

@pytest.fixture
def failing_repository():
    return FailingRepository()

@pytest.fixture
def fake_settings():
    return Settings("host", 4000, "user", "password", "airportdb",
                    "ap-southeast-1", "bucket", "latam-hackathon-005")

@pytest.fixture
def fake_clients():
    return {"tidb": FakeRepository(), "bedrock": FakeBedrockClient(), "storage": FakeStorage()}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_config.py tests/test_models.py -v`

Expected: PASS.

- [ ] **Step 6: Commit the bootstrap contract**

```bash
git add requirements.txt pyproject.toml .gitignore .env.example src/horizon90 tests/test_config.py tests/test_models.py tests/conftest.py
git commit -m "feat: add Horizon 90 application contract"
```

### Task 2: Create the TiDB schema, curated evidence, and vector path

**Files:**
- Create: `sql/schema.sql`
- Create: `src/horizon90/seed.py`
- Create: `src/horizon90/tidb.py`
- Create: `tests/test_seed.py`
- Create: `tests/test_tidb_sql.py`

**Interfaces:**
- Produces `TiDBRepository.connect()`, `TiDBRepository.initialize()`, `TiDBRepository.find_evidence(query: str, limit: int = 3) -> list[Evidence]`, and `TiDBRepository.fetch_exposure(contract: ScenarioContract) -> ExposureSummary`.
- Consumes `Settings` and `ScenarioContract` from Task 1.
- Uses the `airportdb.flight`, `airportdb.airport`, and `airportdb.booking` tables read-only; it never touches passenger detail tables.

- [ ] **Step 1: Write failing seed and SQL safety tests**

```python
from horizon90.seed import CURATED_EVIDENCE, FIXED_STRATEGIES
from horizon90.tidb import EXPOSURE_SQL


def test_seed_has_enough_semantic_evidence():
    assert len(CURATED_EVIDENCE) >= 8
    assert all(item.text and item.source_label for item in CURATED_EVIDENCE)


def test_exposure_query_never_reads_passenger_pii():
    forbidden = ("passenger", "passengerdetails", "employee", "passportno", "emailaddress")
    assert all(token not in EXPOSURE_SQL.lower() for token in forbidden)
    assert "COUNT(DISTINCT b.booking_id)" in EXPOSURE_SQL
    assert len(FIXED_STRATEGIES) == 3
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_seed.py tests/test_tidb_sql.py -v`

Expected: FAIL because the seed and repository modules do not exist.

- [ ] **Step 3: Add the TiDB schema and curated evidence**

```sql
CREATE TABLE IF NOT EXISTS evidence_chunks (
  evidence_id BIGINT AUTO_RANDOM PRIMARY KEY,
  source_label VARCHAR(120) NOT NULL,
  source_type VARCHAR(40) NOT NULL,
  content TEXT NOT NULL,
  s3_key VARCHAR(512) NULL,
  embedding VECTOR(1024) GENERATED ALWAYS AS (
    EMBED_TEXT("tidbcloud_free/amazon/titan-embed-text-v2", content)
  ) STORED,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  VECTOR INDEX evidence_embedding_idx ((VEC_COSINE_DISTANCE(embedding)))
);

CREATE TABLE IF NOT EXISTS scenarios (
  scenario_id BIGINT AUTO_RANDOM PRIMARY KEY,
  airport_iata CHAR(3) NOT NULL,
  start_at DATETIME NOT NULL,
  duration_minutes INT NOT NULL,
  capacity_reduction_pct INT NOT NULL,
  assumptions JSON NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Use ten short Portuguese evidence records in `CURATED_EVIDENCE`, including capacity reduction, transparent communication, connection protection, accessibility, and handoff policy. Define exactly three `Strategy` values in this order: `PROTEGER_CONEXOES`, `PROTEGER_PONTUALIDADE`, and `PRIORIZAR_ATENDIMENTO`.

- [ ] **Step 4: Implement aggregate exposure and vector retrieval**

```python
EXPOSURE_SQL = """
SELECT
  a.iata AS airport_iata,
  COUNT(DISTINCT f.flight_id) AS affected_flights,
  COUNT(DISTINCT b.booking_id) AS affected_bookings,
  COALESCE(SUM(ap.capacity), 0) AS affected_capacity
FROM flight f
JOIN airport a ON a.airport_id IN (f.`from`, f.`to`)
LEFT JOIN booking b ON b.flight_id = f.flight_id
LEFT JOIN airplane ap ON ap.airplane_id = f.airplane_id
WHERE a.iata = %s
  AND (f.departure < %s AND f.arrival >= %s)
GROUP BY a.iata
"""

VECTOR_SQL = """
SELECT evidence_id, source_label, source_type, content,
       VEC_EMBED_COSINE_DISTANCE(
         embedding,
         EMBED_TEXT("tidbcloud_free/amazon/titan-embed-text-v2", %s)
       ) AS distance
FROM evidence_chunks
ORDER BY distance
LIMIT %s
"""
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_seed.py tests/test_tidb_sql.py -v`

Expected: PASS.

- [ ] **Step 6: Ask the user for the first browser action, then run the live TiDB check**

Ask the user to create the TiDB Cloud Starter cluster in AWS São Paulo, obtain the public endpoint credentials, and place them only in local `.env`. Then run:

```bash
python -c "from horizon90.config import Settings; from horizon90.tidb import TiDBRepository; r=TiDBRepository(Settings.from_env()); r.initialize(); print(r.find_evidence('redução de capacidade no aeroporto'))"
```

Expected: a non-empty semantic evidence result and no secret in terminal output.

- [ ] **Step 7: Commit the TiDB and vector layer**

```bash
git add sql/schema.sql src/horizon90/seed.py src/horizon90/tidb.py tests/test_seed.py tests/test_tidb_sql.py
git commit -m "feat: add TiDB exposure and vector evidence"
```

### Task 3: Add Bedrock parsing with a safe deterministic fallback

**Files:**
- Create: `src/horizon90/bedrock.py`
- Create: `tests/test_bedrock.py`
- Modify: `src/horizon90/models.py`

**Interfaces:**
- Produces `BedrockClient.parse_scenario(description: str, fallback: ScenarioContract) -> ScenarioContract` and `BedrockClient.invoke_json(prompt: str, model_id: str) -> dict[str, object]`.
- Consumes `ScenarioContract` from Task 1.
- Returns the supplied fallback unchanged when the model response is unavailable or fails schema validation.

- [ ] **Step 1: Write failing model-response tests**

```python
from horizon90.bedrock import BedrockClient
from horizon90.models import ScenarioContract


def test_parse_scenario_uses_valid_json_response(fake_runtime):
    fake_runtime.text = '{"airport_iata":"GRU","duration_minutes":90,"capacity_reduction_pct":30}'
    result = BedrockClient(fake_runtime).parse_scenario("GRU perde 30%", seeded_contract())
    assert result.airport_iata == "GRU"
    assert result.duration_minutes == 90


def test_parse_scenario_returns_seed_when_json_is_invalid(fake_runtime):
    fake_runtime.text = "não é JSON"
    seed = seeded_contract()
    assert BedrockClient(fake_runtime).parse_scenario("texto", seed) == seed
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_bedrock.py -v`

Expected: FAIL because `BedrockClient` does not exist.

- [ ] **Step 3: Implement direct Bedrock invocation and schema validation**

```python
HAIKU_ID = "anthropic.claude-3-haiku-20240307-v1:0"
SONNET_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"

def invoke_json(self, prompt: str, model_id: str = HAIKU_ID) -> dict[str, object]:
    response = self.runtime.invoke_model(
        modelId=model_id,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 700,
            "messages": [{"role": "user", "content": prompt}],
        }),
    )
    text = json.loads(response["body"].read())["content"][0]["text"]
    return json.loads(extract_json_object(text))
```

The prompt must request only airport IATA, start time, duration, reduction percentage, and `assumptions`. It must say: "Não invente valores ausentes; devolva null quando não houver base."

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_bedrock.py -v`

Expected: PASS.

- [ ] **Step 5: Ask the user for the Bedrock browser action, then run the live check**

Ask the user to complete MFA and provide the Group 5 Bedrock key by placing it in `.env` only. Run:

```bash
python -c "from horizon90.bedrock import BedrockClient; print(BedrockClient.from_env().parse_scenario('GRU perde 30% de capacidade por 90 minutos', seeded_contract()))"
```

Expected: a parsed contract or the explicitly marked seeded fallback, with no key printed.

- [ ] **Step 6: Commit the Bedrock adapter**

```bash
git add src/horizon90/bedrock.py src/horizon90/models.py tests/test_bedrock.py
git commit -m "feat: add Bedrock scenario parser"
```

### Task 4: Implement fixed strategies and the concurrent four-role rehearsal

**Files:**
- Create: `src/horizon90/rehearsal.py`
- Create: `tests/test_rehearsal.py`
- Modify: `src/horizon90/seed.py`

**Interfaces:**
- Produces `run_rehearsal(contract: ScenarioContract, exposure: ExposureSummary, evidence: list[Evidence], bedrock: BedrockClient) -> list[AgentReaction]`.
- Produces `build_decision_pack(contract: ScenarioContract, exposure: ExposureSummary, evidence: list[Evidence], reactions: list[AgentReaction], selected_strategy_id: str, bedrock: BedrockClient) -> DecisionPack`.
- Consumes the fixed `Strategy` and `ActorDefinition` arrays in `seed.py`.

- [ ] **Step 1: Write failing rehearsal tests**

```python
from horizon90.rehearsal import run_rehearsal


def test_rehearsal_returns_one_reaction_per_fixed_actor(fake_bedrock):
    reactions = run_rehearsal(seeded_contract(), seeded_exposure(), seeded_evidence(), fake_bedrock)
    assert [reaction.actor_id for reaction in reactions] == [
        "airline_ops", "airport_duty_manager", "short_connection_passenger", "customer_service"
    ]
    assert all(reaction.round_number == 1 for reaction in reactions)


def test_rehearsal_rejects_personal_data_in_prompt(fake_bedrock):
    run_rehearsal(seeded_contract(), seeded_exposure(), seeded_evidence(), fake_bedrock)
    assert "passport" not in fake_bedrock.prompts[0].lower()
    assert "emailaddress" not in fake_bedrock.prompts[0].lower()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_rehearsal.py -v`

Expected: FAIL because the rehearsal module does not exist.

- [ ] **Step 3: Implement the four fixed actors and concurrent execution**

```python
ACTORS = [
    ActorDefinition("airline_ops", "Operações da companhia", "proteger a malha e limitar propagação"),
    ActorDefinition("airport_duty_manager", "Gestão aeroportuária", "preservar segurança e capacidade"),
    ActorDefinition("short_connection_passenger", "Passageiro com conexão curta", "evitar perda de conexão e falta de informação"),
    ActorDefinition("customer_service", "Atendimento ao cliente", "manter comunicação viável e consistente"),
]

with ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(run_actor, actor, contract, exposure, evidence, bedrock) for actor in ACTORS]
    reactions = [future.result(timeout=20) for future in futures]
```

Every actor response must validate into `AgentReaction` with `likely_reaction`, `objection`, `pressure_signal`, and `validation_question`. If a role invocation fails, return a response with `availability="unavailable"` and a non-LLM explanation.

- [ ] **Step 4: Implement final decision-pack synthesis only after selection**

```python
def build_decision_pack(
    contract: ScenarioContract,
    exposure: ExposureSummary,
    evidence: list[Evidence],
    reactions: list[AgentReaction],
    selected_strategy_id: str,
    bedrock: BedrockClient,
) -> DecisionPack:
    selected = next(strategy for strategy in FIXED_STRATEGIES if strategy.id == selected_strategy_id)
    return bedrock.synthesize_decision_pack(
        contract=contract, exposure=exposure, evidence=evidence,
        reactions=reactions, selected_strategy=selected,
    )
```

The final Sonnet prompt must require `recommended_action`, `tradeoffs`, `evidence_ids`, `assumptions`, and `human_validation_questions`. It must prohibit claims that a flight was actually cancelled, delayed, or rebooked.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_rehearsal.py -v`

Expected: PASS.

- [ ] **Step 6: Commit the rehearsal service**

```bash
git add src/horizon90/rehearsal.py src/horizon90/seed.py tests/test_rehearsal.py
git commit -m "feat: add multi-agent decision rehearsal"
```

### Task 5: Add S3 replay storage and a service-level orchestration boundary

**Files:**
- Create: `src/horizon90/storage.py`
- Create: `src/horizon90/service.py`
- Create: `tests/test_storage.py`
- Create: `tests/test_service.py`

**Interfaces:**
- Produces `ReplayStorage.write(pack: DecisionPack) -> ArchiveResult`.
- Produces `HorizonService.run(contract: ScenarioContract) -> RunResult` and `HorizonService.select_strategy(run_id: str, strategy_id: str) -> DecisionPack`.
- `ArchiveResult` exposes `status` as `archived` or `not_archived`; no call silently pretends to save an S3 object.

- [ ] **Step 1: Write failing storage and orchestration tests**

```python
from horizon90.storage import ReplayStorage


def test_storage_uses_only_group_five_prefix(fake_s3, decision_pack):
    result = ReplayStorage(fake_s3, "bucket", "latam-hackathon-005").write(decision_pack)
    assert result.status == "archived"
    assert fake_s3.key.startswith("latam-hackathon-005/replays/")


def test_service_labels_vector_fallback_when_repository_fails(failing_repository, fake_bedrock):
    result = HorizonService(failing_repository, fake_bedrock, fake_storage()).run(seeded_contract())
    assert result.integration_status.tidb == "fallback"
    assert result.integration_status.vector == "fallback"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_storage.py tests/test_service.py -v`

Expected: FAIL because storage and service modules do not exist.

- [ ] **Step 3: Implement replay serialization and integration status**

```python
def write(self, pack: DecisionPack) -> ArchiveResult:
    return self.write_json(pack.decision_id, pack.model_dump())

def write_json(self, replay_id: str, payload: dict[str, object]) -> ArchiveResult:
    key = f"{self.prefix}/replays/{replay_id}.json"
    try:
        self.client.put_object(Bucket=self.bucket, Key=key,
                               Body=json.dumps(payload, ensure_ascii=False, indent=2),
                               ContentType="application/json")
        return ArchiveResult(status="archived", s3_key=key)
    except ClientError as exc:
        return ArchiveResult(status="not_archived", message=exc.response["Error"]["Code"])
```

`HorizonService.run()` must call exposure, vector retrieval, and rehearsal in that order. It must preserve a per-service `IntegrationStatus` object so the UI can show `real`, `fallback`, or `unavailable` for TiDB, vector, Bedrock, and S3.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_storage.py tests/test_service.py -v`

Expected: PASS.

- [ ] **Step 5: Commit storage and orchestration**

```bash
git add src/horizon90/storage.py src/horizon90/service.py tests/test_storage.py tests/test_service.py
git commit -m "feat: archive decision replays and statuses"
```

### Task 6: Build the one-screen FastAPI console and API

**Files:**
- Create: `src/horizon90/main.py`
- Create: `src/horizon90/static/index.html`
- Create: `src/horizon90/static/app.js`
- Create: `src/horizon90/static/styles.css`
- Create: `tests/test_api.py`

**Interfaces:**
- Produces `GET /health`, `GET /api/seed`, `POST /api/runs`, `POST /api/runs/{run_id}/decision`, and `GET /`.
- Consumes `HorizonService` from Task 5.
- Returns API failures as JSON with `status`, `message`, and no secret or stack trace.

- [ ] **Step 1: Write failing API tests**

```python
from fastapi.testclient import TestClient
from horizon90.main import create_app


def test_seed_endpoint_returns_confirmed_gru_scenario(fake_service):
    client = TestClient(create_app(fake_service))
    response = client.get("/api/seed")
    assert response.status_code == 200
    assert response.json()["airport_iata"] == "GRU"
    assert response.json()["confirmed"] is True


def test_run_endpoint_requires_confirmed_contract(fake_service):
    client = TestClient(create_app(fake_service))
    response = client.post("/api/runs", json={"airport_iata": "GRU", "confirmed": False})
    assert response.status_code == 422
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_api.py -v`

Expected: FAIL because the FastAPI application does not exist.

- [ ] **Step 3: Implement routes and static asset serving**

```python
def create_app(service: HorizonService) -> FastAPI:
    app = FastAPI(title="Horizon 90")
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/runs", response_model=RunResult)
    def create_run(payload: ScenarioInput) -> RunResult:
        return service.run(payload.to_contract())
    return app
```

The interface must contain exactly these regions: a scenario form; an integration-status strip; exposure metrics; three fixed strategy cards; four actor reactions; a button to generate the selected decision pack; and an explicit simulated/fallback label. Use no raw passenger detail and no MiroFish integration claim.

- [ ] **Step 4: Add browser-native interactions in `app.js`**

```javascript
async function runScenario() {
  const response = await fetch('/api/runs', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(readScenario())});
  const result = await response.json();
  renderIntegrationStatus(result.integration_status);
  renderExposure(result.exposure);
  renderStrategies(result.strategies);
  renderReactions(result.reactions);
}
```

Disable the decision-pack button until one strategy is selected. Render `not_archived`, `fallback`, and `unavailable` visibly rather than hiding them.

- [ ] **Step 5: Run API tests and a local browser smoke test**

Run: `python -m pytest tests/test_api.py -v`

Expected: PASS.

Run: `uvicorn horizon90.main:app --host 127.0.0.1 --port 8000`

Expected: `GET /health` returns `{"status":"ok"}` and the seeded flow renders without console errors.

- [ ] **Step 6: Commit the console**

```bash
git add src/horizon90/main.py src/horizon90/static tests/test_api.py
git commit -m "feat: add Horizon 90 decision console"
```

### Task 7: Add preflight, Kiro evidence, submission proof, deployment, and end-to-end verification

**Files:**
- Create: `scripts/preflight.py`
- Create: `.kiro/specs/horizon-90/requirements.md`
- Create: `.kiro/specs/horizon-90/design.md`
- Create: `.kiro/specs/horizon-90/tasks.md`
- Create: `SUBMISSION.md`
- Create: `README.md`
- Create: `tests/test_preflight.py`

**Interfaces:**
- Produces `run_preflight(settings: Settings) -> dict[str, str]` with keys `tidb`, `vector`, `bedrock`, and `s3`.
- Produces deploy instructions that use HTTPS GitHub cloning, Python 3.11, `.env` on EC2 only, `setsid nohup`, `0.0.0.0`, and port 8501 or 8000.

- [ ] **Step 1: Write the failing preflight test**

```python
from scripts.preflight import run_preflight


def test_preflight_reports_each_dependency_without_stopping(fake_settings, fake_clients):
    result = run_preflight(fake_settings, **fake_clients)
    assert result == {"tidb": "ok", "vector": "ok", "bedrock": "ok", "s3": "ok"}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_preflight.py -v`

Expected: FAIL because `scripts/preflight.py` does not exist.

- [ ] **Step 3: Implement each live preflight check independently**

```python
def run_preflight(settings, tidb=None, bedrock=None, storage=None):
    result = {}
    try:
        repository = tidb or TiDBRepository(settings)
        repository.ping()
        result["tidb"] = "ok"
        result["vector"] = "ok" if repository.find_evidence("redução de capacidade", 1) else "failed"
    except Exception:
        result["tidb"] = result["vector"] = "failed"
    try:
        (bedrock or BedrockClient.from_env()).invoke_json('{"check":"ping"}')
        result["bedrock"] = "ok"
    except Exception:
        result["bedrock"] = "failed"
    try:
        (storage or ReplayStorage.from_settings(settings)).write_json("preflight", {"check": "ok"})
        result["s3"] = "ok"
    except Exception:
        result["s3"] = "failed"
    return result
```

- [ ] **Step 4: Write the Kiro and submission files with exact evidence paths**

`SUBMISSION.md` must identify:

```markdown
## Stack - marque o que você realmente usou
- [ ] TiDB Cloud Starter na AWS sa-east-1
- [ ] Busca vetorial no TiDB (coluna VECTOR ou EMBED_TEXT)
- [ ] Amazon Bedrock (ap-southeast-1)
- [ ] Publicado na AWS -> URL no ar:
- [ ] Construído com Kiro (.kiro/ commitado)

## Onde olhar
Conexão/consultas TiDB: src/horizon90/tidb.py
Busca vetorial: sql/schema.sql e src/horizon90/tidb.py
Chamadas ao Bedrock: src/horizon90/bedrock.py
```

Mark a checkbox only after its preflight or deployment verification passes. The README must include the local command and the EC2 command:

```bash
setsid nohup python3.11 -m uvicorn horizon90.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 < /dev/null &
```

- [ ] **Step 5: Run the test suite and static checks**

Run: `python -m pytest -v`

Expected: PASS.

Run: `python -m compileall src scripts`

Expected: PASS with no syntax errors.

- [ ] **Step 6: Ask the user for the final browser actions and deploy**

Ask the user to:

1. create the Group 5 TiDB Cloud Starter cluster in AWS São Paulo and enter credentials in the EC2 `.env`;
2. complete AWS MFA and enter the Group 5 Bedrock key only in the EC2 `.env`;
3. open the Group 5 EC2 Session Manager connection;
4. create the public Group 5 GitHub repository before cloning it onto EC2.

After the user completes those actions, run `python scripts/preflight.py`, deploy with the exact command above, open the public URL, execute the seeded scenario, generate a decision pack, and confirm the resulting replay key is under the Group 5 prefix.

- [ ] **Step 7: Commit delivery evidence**

```bash
git add scripts/preflight.py .kiro SUBMISSION.md README.md tests/test_preflight.py
git commit -m "docs: add deployment and submission evidence"
```

## Plan Self-Review

### Spec coverage

- One FastAPI process and static console: Task 6.
- TiDB Cloud state and aggregate airport baseline: Task 2.
- TiDB auto-embedding and visible semantic query: Task 2 plus Task 7 preflight.
- Bedrock region, model separation, and fallback: Task 3 and Task 4.
- Four-role one-round MiroFish-inspired rehearsal: Task 4.
- S3 team-prefix replay and truthful status: Task 5 and Task 7.
- PII avoidance: Task 2 SQL safety test, Task 4 prompt test, and Task 6 UI rules.
- Kiro, public-repo evidence, submission file, EC2 deployment, and demo readiness: Task 7.

### Placeholder scan

The plan contains no unresolved implementation placeholders. Every browser-dependent action is named as a user-owned access step and has a precise verification command or expected result.

### Type consistency

`Settings`, `ScenarioInput`, `ScenarioContract`, `ExposureSummary`, `Strategy`, `Evidence`, `AgentReaction`, `DecisionPack`, `ArchiveResult`, `RunResult`, and `IntegrationStatus` are introduced in Tasks 1 and 2 before later tasks consume them. API routes consume `ScenarioInput` and return `RunResult` or `DecisionPack`; the browser consumes those same JSON structures.
