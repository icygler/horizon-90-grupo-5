# Horizon 90 — Airport Digital Rehearsal

Horizon 90 é uma aplicação de IA generativa para ensaiar decisões aeroportuárias a partir de um cenário histórico simulado. Para o exercício-semente, GRU perde 30% de capacidade durante 90 minutos em `2015-06-04T15:00:00`.

Ela combina agregados do `airportdb`, evidência semântica no TiDB Vector, quatro reações de papéis fixos inspiradas no MiroFish e um pacote de decisão revisável. Não é previsão, status ao vivo, cancelamento ou remarcação real.

## Segurança e limites

- O código consulta somente agregados de `flight`, `airport`, `booking` e `airplane`.
- Dados de passageiro e empregado não entram em SQL, prompts, respostas, logs ou Git.
- Fallback e indisponibilidade ficam visíveis na interface.
- Replays S3 são limitados ao prefixo do Grupo 5: `latam-hackathon-005/`.

## Executar localmente

Use Python 3.11+:

```bash
python -m pip install -r requirements.txt
python -m pytest -v
python -m uvicorn horizon90.main:app --app-dir src --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000`. Sem `.env`, a demonstração continua disponível com dados locais e estados honestos de fallback/indisponível.

## Configuração ao vivo

Copie `.env.example` para `.env` e preencha apenas localmente, sem versionar:

- `TIDB_HOST`, `TIDB_USER`, `TIDB_PASSWORD`, `TIDB_DATABASE`
- `AWS_BEARER_TOKEN_BEDROCK`

O S3 já usa o bucket do evento e o prefixo reservado ao Grupo 5. Crie o cluster TiDB Cloud Starter em AWS São Paulo e carregue o `airportdb` antes do preflight.

```bash
python scripts/preflight.py
```

O preflight imprime somente os estados `ok` ou `failed`; nunca imprime segredos.

## Deploy no EC2 do evento

No EC2 do Grupo 5, conecte-se por Session Manager, clone o repositório público por HTTPS e mantenha o `.env` somente na instância:

```bash
python3.11 -m pip install -r requirements.txt
setsid nohup python3.11 -m uvicorn horizon90.main:app --app-dir src --host 0.0.0.0 --port 8000 > app.log 2>&1 < /dev/null &
```

Execute `python3.11 scripts/preflight.py` antes do demo. Em seguida acesse a porta pública autorizada pelo evento e registre a URL em `SUBMISSION.md`.

## Evidências de hackathon

Consulte `SUBMISSION.md` para as evidências por item de pontuação. As caixas ficam desmarcadas até a validação real correspondente.
