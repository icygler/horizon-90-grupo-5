# Horizon 90 — Design entregue

## Decisão de produto

Horizon 90 é um ensaio de decisão para operadores aeroportuários diante de uma redução de capacidade. A aplicação não prevê o futuro nem dispara ações externas. Ela usa um recorte histórico, transforma o cenário em exposição operacional e organiza uma resposta humana por tempo.

## Arquitetura implementada

```text
airportdb → TiDB (agregados) → TiDB Vector (evidências)
                                      ↓
                      OpenAI Responses / GPT-5.6 Luna
                                      ↓
             folha de resposta + arquivo local em tmp/replays/
```

- Um processo FastAPI serve a capa de pitch e o console em rotas separadas.
- TiDB fornece somente agregados de voo, reserva e capacidade.
- TiDB Vector traz evidências semânticas curadas.
- GPT-5.6 Luna produz quatro perspectivas e, após escolha humana de estratégia, ações para agora, 15 min, 30 min e fim da janela.
- O pacote fica registrado localmente. Não há S3, Bedrock, EC2 ou deploy AWS nesta entrega.

## Limites

O cenário-semente é GRU em `2015-06-04T15:00:00`, com 90 minutos e 30% de capacidade indisponível. É uma simulação histórica. Dados pessoais de passageiro e empregado não entram em consultas, prompts, respostas ou logs.
