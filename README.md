# Horizon 90 — Airport Digital Rehearsal

> Grupo 5 · [guia de avaliação](EVALUATION.md) · [submissão](SUBMISSION.md)

Horizon 90 é uma aplicação de IA generativa para ensaiar decisões em situações de redução da capacidade aeroportuária. Em vez de prever a operação ao vivo ou executar remarcações, ela organiza uma decisão humana: mede a exposição histórica, contrapõe perspectivas operacionais e entrega uma folha de resposta para os próximos minutos.

## Cenário demonstrável

**GRU · 04/06/2015 às 15:00 · 90 minutos · 30% de capacidade indisponível.**

O dado vem do `airportdb` como referência histórica. O rótulo **Simulação histórica** está sempre visível: não há alteração em voos, passageiros ou sistemas externos.

## O que a equipe avaliadora pode ver

| Superfície | Endereço local | Finalidade |
| --- | --- | --- |
| Capa de pitch | `http://127.0.0.1:8000` | Problema, ideia, arquitetura, valor e equipe. |
| Console operacional | `http://127.0.0.1:8000/console` | Configuração do cenário, impacto, estratégias e folha de resposta. |

O console conduz quatro etapas: **configurar → simular → comparar → decidir**. A folha de resposta mostra ações para agora, 15 min, 30 min e fim da janela, responsáveis sugeridos, sinais de avanço, impactos a acompanhar e a próxima reavaliação. Todas as ações exigem validação humana.

## Stack entregue e estado real

- **TiDB Cloud Starter** em `sa-east-1`, com `airportdb` importado.
- **TiDB Vector** com `VECTOR(1024)` e `EMBED_TEXT` para evidências semânticas.
- **OpenAI Responses / GPT-5.6 Luna** para a rodada multiagente e a folha de resposta estruturada.
- **FastAPI + HTML/CSS/JavaScript** executados localmente.
- **Registro local** dos pacotes em `tmp/replays/`.
- **Kiro**: requisitos, design e tarefas em [`.kiro/specs/horizon-90/`](.kiro/specs/horizon-90/).

Amazon Bedrock, EC2/AWS público e S3 **não são utilizados nem alegados como parte desta entrega**.

## Executar localmente

Use Python 3.11+:

```bash
python -m pip install -r requirements.txt
python -m pytest -v
python -m uvicorn horizon90.main:app --app-dir src --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000`.

### Caminho com integrações ao vivo

Copie `.env.example` para `.env` e preencha apenas localmente, sem versionar:

```env
TIDB_HOST=
TIDB_PORT=4000
TIDB_USER=
TIDB_PASSWORD=
TIDB_DATABASE=airportdb
OPENAI_API_KEY=
```

Depois, execute:

```bash
python scripts/import_airportdb.py
python scripts/preflight.py
```

Sem credenciais, o app continua navegável com estados honestos de fallback ou indisponibilidade. O preflight nunca imprime segredos.

## Arquitetura

```text
airportdb → TiDB (agregados) → TiDB Vector (evidências)
                                      ↓
                         OpenAI GPT-5.6 Luna
                                      ↓
                    decisão humana + registro local
```

Os arquivos mais importantes para revisão estão em:

- `src/horizon90/tidb.py` — consultas agregadas e busca vetorial.
- `sql/schema.sql` — vetor e auto-embedding.
- `src/horizon90/openai_client.py` — Responses API e JSON estruturado.
- `src/horizon90/rehearsal.py` — rodada inspirada no MiroFish e plano temporal.
- `src/horizon90/storage.py` — registro local do pacote.
- `src/horizon90/static/` — capa do pitch e console operacional.

## Segurança e limites

- O código consulta somente agregados de `flight`, `airport`, `booking` e `airplane`.
- Dados de passageiro e empregado não entram em SQL da aplicação, prompts, respostas, logs ou Git.
- O uso de MiroFish é inspiração para o padrão multiagente; não há runtime integrado do MiroFish.
- A aplicação não é um sistema de previsão, status ao vivo, cancelamento ou remarcação.
