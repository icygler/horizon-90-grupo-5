# Horizon 90 — Grupo 5

## Equipe

- Israel Cygler
- Gustavo Tinoco
- Wesley Ribeiro
- Rafaeli Gil

## Repositório público

https://github.com/icygler/horizon-90-grupo-5

## O que construímos

**Horizon 90** é um ensaio de decisão aeroportuária com IA generativa. A aplicação usa um recorte histórico do `airportdb` para simular uma redução de capacidade e apoiar a decisão humana, sem alterar operação real, previsão ou remarcação.

O cenário demonstrável é: **GRU, 04/06/2015 às 15:00, 90 minutos, 30% de capacidade indisponível**. A interface conduz o operador por quatro etapas: configurar, simular, comparar estratégias e gerar um pacote revisável de decisão.

## Stack e evidências — marque apenas o que foi validado

- [x] TiDB Cloud Starter em AWS `sa-east-1`, com `airportdb` importado
- [x] Busca vetorial no TiDB com `VECTOR(1024)` e `EMBED_TEXT`
- [x] OpenAI Responses com GPT-5.6 Luna para a rodada multiagente e o pacote de decisão
- [x] Execução local da aplicação FastAPI em `http://127.0.0.1:8000`
- [x] Registro local de pacotes de decisão em `tmp/replays/`
- [x] Especificações do Kiro em `.kiro/` versionadas
- [ ] Amazon Bedrock — não utilizado nesta entrega
- [ ] Deploy público na AWS/EC2 — não realizado; a demonstração é local
- [ ] Arquivamento de replay no S3 — não utilizado nesta entrega

## Arquitetura entregue

1. A aplicação FastAPI, executada localmente, recebe os parâmetros do cenário.
2. O TiDB consulta somente agregados do `airportdb` para calcular exposição de voos, reservas e capacidade.
3. O TiDB Vector recupera evidências semânticas para contextualizar a rodada.
4. O GPT-5.6 Luna gera quatro perspectivas operacionais e, após uma escolha humana de estratégia, um pacote de decisão estruturado.
5. A interface mostra origem dos dados, estados das integrações, evidências, trade-offs, ações temporais, responsáveis sugeridos, impacto a acompanhar e perguntas de validação humana.

## Onde olhar no código

- Conexão e consultas agregadas ao TiDB: `src/horizon90/tidb.py`
- Esquema e auto-embedding vetorial: `sql/schema.sql`
- OpenAI Responses, GPT-5.6 Luna e JSON estruturado: `src/horizon90/openai_client.py`
- Rodada multiagente inspirada no MiroFish: `src/horizon90/rehearsal.py`
- Orquestração e estados de integração: `src/horizon90/service.py`
- Interface e fluxo de decisão: `src/horizon90/static/`
- Preflight independente: `scripts/preflight.py`
- Cobertura de testes e bloqueio de PII: `tests/`

## Como executar localmente

Use Python 3.11+ e mantenha credenciais somente no arquivo `.env` local, nunca no Git:

```bash
python -m pip install -r requirements.txt
python -m pytest -v
python -m uvicorn horizon90.main:app --app-dir src --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000`.

Para o caminho ao vivo, configure `TIDB_HOST`, `TIDB_USER`, `TIDB_PASSWORD`, `TIDB_DATABASE` e `OPENAI_API_KEY` no `.env`. Sem credenciais, a interface preserva estados explícitos de fallback ou indisponibilidade.

## Roteiro de demonstração

1. Abra a execução local e confirme o rótulo **Simulação histórica**.
2. Ajuste os controles: aeroporto, recorte histórico, janela de impacto e capacidade indisponível.
3. Execute o cenário-semente e mostre a exposição agregada e as evidências do TiDB/TiDB Vector.
4. Compare as três opções de resposta e as quatro perspectivas operacionais geradas pela IA.
5. Selecione uma estratégia e gere o pacote revisável de decisão.
6. Mostre a área de rastreabilidade: TiDB, Vector, OpenAI e o registro local ficam identificados; Bedrock, deploy AWS e S3 não são alegados como entregues.

## Limites e proteção de dados

- A aplicação não é um sistema operacional ao vivo e não realiza ações externas.
- Consultas e prompts usam somente agregados de `flight`, `airport`, `booking` e `airplane`.
- Dados de passageiro e empregado não entram em SQL da aplicação, prompts, respostas, logs ou repositório.
- O uso de MiroFish é de inspiração para o padrão de rodada multiagente; não há runtime integrado do MiroFish.
