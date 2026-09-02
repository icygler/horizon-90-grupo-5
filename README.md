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
- `OPENAI_API_KEY` (GPT-5.6 Luna via Responses API)

Nesta entrega, a aplicação é executada localmente. O TiDB Cloud é o banco gerenciado usado pela aplicação; OpenAI Responses é o provedor de IA generativa. Amazon Bedrock, EC2 e o replay S3 não são requisitos da demonstração entregue e não devem ser apresentados como integrações ativas.

```bash
python scripts/import_airportdb.py
python scripts/preflight.py
```

O preflight imprime somente os estados `ok` ou `failed`; nunca imprime segredos.

### Alternativa sem IAM para importação

Caso a conta do evento não permita criar a IAM Role que o importador gerenciado do TiDB exige, use o importador TLS direto incluído no repositório. Ele lê o dump oficial em `tmp/data/hackathon_airportdb.sql.gz`, usa somente as variáveis TiDB do `.env` local e não registra linhas do dataset:

```bash
python scripts/import_airportdb.py
```

Depois de importar, inicie o app uma vez com o `.env` preenchido. Ele consulta apenas agregados do `airportdb` e mantém os estados das integrações explícitos na tela.

## Escopo de execução desta entrega

A demonstração é local, em `http://127.0.0.1:8000`; não há URL pública, deploy em EC2/AWS ou chamada ao Amazon Bedrock nesta versão. Isso é intencionalmente declarado em `SUBMISSION.md` para que a evidência do hackathon corresponda ao estado real do projeto.

Com o `.env` configurado, use `python scripts/preflight.py` antes da apresentação para verificar as dependências locais. O resultado de cada integração permanece visível na interface como `verificado`, `alternativo` ou `indisponível`.

## Evidências de hackathon

Consulte `SUBMISSION.md` para as evidências por item de pontuação. As caixas ficam desmarcadas até a validação real correspondente.
