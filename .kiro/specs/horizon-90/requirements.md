# Horizon 90 — Requisitos entregues

## Objetivo

Facilitar a decisão humana quando a capacidade operacional de um aeroporto é reduzida por um período definido.

## Critérios de aceitação

- O cenário é visivelmente histórico e simulado, e exige confirmação.
- O operador altera aeroporto, recorte histórico, janela de impacto e capacidade indisponível.
- A exposição usa somente agregados; nenhum dado pessoal é consultado ou enviado ao modelo.
- TiDB Vector recupera evidências semânticas para a rodada.
- A aplicação compara três estratégias através de quatro papéis fixos inspirados no MiroFish, sem alegar integração do runtime MiroFish.
- A folha de resposta só é gerada após a escolha humana de uma estratégia.
- A folha contém ações temporais, responsável sugerido, sinal de avanço, impactos e próxima reavaliação.
- O pacote é registrado localmente e os estados das integrações são explícitos.
- A capa de pitch apresenta ideia, arquitetura, cenário, valor e integrantes antes do console.

## Fora de escopo

Amazon Bedrock, S3, EC2/AWS público, rebooking, cancelamento, previsão ao vivo e qualquer execução automática na operação.
