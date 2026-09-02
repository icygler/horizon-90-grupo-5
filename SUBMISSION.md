# Horizon 90 — Grupo 5

## Repositório público

https://github.com/icygler/horizon-90-grupo-5

## Stack — marque apenas o que foi validado ao vivo

- [x] TiDB Cloud Starter na AWS `sa-east-1`
- [x] Busca vetorial no TiDB com `VECTOR(1024)` e `EMBED_TEXT`
- [ ] Amazon Bedrock em `ap-southeast-1`
- [ ] Publicado na AWS — URL no ar:
- [x] GPT-5.6 Luna via OpenAI Responses (execução local)
- [x] Evidências de especificação em `.kiro/` commitadas

## Onde olhar

- Conexão e agregados TiDB: `src/horizon90/tidb.py`
- Esquema e auto-embedding vetorial: `sql/schema.sql`
- OpenAI Responses, GPT-5.6 Luna e JSON estruturado: `src/horizon90/openai_client.py`
- Rehearsal inspirado no MiroFish: `src/horizon90/rehearsal.py`
- Prefixo S3 do Grupo 5: `src/horizon90/storage.py`
- Preflight independente: `scripts/preflight.py`
- Cobertura de testes e bloqueio de PII: `tests/`

## Demonstração

1. Abra a URL pública após o deploy.
2. Execute o cenário GRU de 90 minutos e redução de 30%.
3. Mostre os estados de integração, as evidências semânticas e as quatro reações.
4. Selecione uma estratégia, gere o pacote e mostre o estado do replay S3.

Não marque um item acima se o preflight ou deploy correspondente ainda não passou.
