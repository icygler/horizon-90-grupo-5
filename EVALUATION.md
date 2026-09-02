# Guia de avaliação — Horizon 90

## Grupo 5

- Israel Cygler
- Gustavo Tinoco
- Wesley Ribeiro
- Rafaeli Gil

## Em uma frase

**Horizon 90 transforma uma redução histórica de capacidade aeroportuária em uma folha de resposta humana, com exposição, trade-offs, ações temporais e pontos de reavaliação.**

## Comece aqui

1. Leia o [README](README.md) para executar localmente.
2. Abra a capa de pitch em `http://127.0.0.1:8000`.
3. Abra o console em `http://127.0.0.1:8000/console`.
4. Execute o cenário-semente GRU / 90 min / 30%.
5. Selecione uma estratégia e gere a folha de resposta.

## O que foi implementado e validado

| Critério | Evidência no repositório |
| --- | --- |
| Dataset aeroportuário e agregados | `src/horizon90/tidb.py`, `scripts/import_airportdb.py` |
| Busca semântica vetorial | `sql/schema.sql`, `src/horizon90/tidb.py` |
| IA generativa estruturada | `src/horizon90/openai_client.py`, `src/horizon90/rehearsal.py` |
| Rodada com quatro perspectivas | `src/horizon90/seed.py`, `src/horizon90/rehearsal.py` |
| Próximas ações e gates de revisão | `DecisionPack` em `src/horizon90/models.py` e console em `src/horizon90/static/app.js` |
| Registro local verificável | `src/horizon90/storage.py`, `tests/test_storage.py` |
| Pitch, experiência e responsividade | `src/horizon90/static/pitch.html`, `index.html`, `styles.css` |
| Testes automatizados | `tests/` — `python -m pytest -v` |
| Kiro | `.kiro/specs/horizon-90/` |

## Estado das integrações

| Integração | Estado da entrega |
| --- | --- |
| TiDB Cloud / airportdb | Usado e validado no caminho ao vivo. |
| TiDB Vector | Usado e validado no caminho ao vivo. |
| OpenAI GPT-5.6 Luna | Usado para o caminho ao vivo; se a chave não estiver no `.env`, a interface declara a indisponibilidade. |
| Registro local | Usado; cada pacote fica em `tmp/replays/`. |
| Amazon Bedrock | Não utilizado. |
| EC2 / URL pública AWS | Não utilizado; demonstração local. |
| S3 | Não utilizado. |

## Roteiro de dois minutos

1. Na capa, explique que a decisão precisa ganhar tempo quando a capacidade cai.
2. Mostre o cenário GRU e os quatro controles que o operador pode alterar.
3. Execute a simulação e explique exposição, estratégias e perspectivas.
4. Escolha uma estratégia e apresente as ações por tempo, donos sugeridos, impactos e reavaliação.
5. Feche reforçando: o sistema prepara a decisão; a operação humana valida e executa.

## Integridade e privacidade

- Dados pessoais de passageiros e empregados ficam fora de consultas, prompts, respostas e logs.
- O cenário é histórico e simulado; não há automação de ação operacional.
- Estados de indisponibilidade e fallback são mostrados ao operador em vez de mascarados.
