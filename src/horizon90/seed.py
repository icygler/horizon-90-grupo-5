"""Curated, non-personal data used when a live dependency is unavailable."""

from dataclasses import dataclass

from horizon90.models import Strategy


@dataclass(frozen=True)
class CuratedEvidence:
    source_label: str
    source_type: str
    text: str


CURATED_EVIDENCE = [
    CuratedEvidence("Capacidade", "simulation", "Redução temporária de capacidade exige priorização explícita."),
    CuratedEvidence("Conexões", "policy", "Conexões curtas devem ser identificadas antes de comunicar mudanças."),
    CuratedEvidence("Comunicação", "policy", "Comunicação transparente deve informar impacto, hipótese e próximo ponto de atualização."),
    CuratedEvidence("Atendimento", "policy", "Atendimento precisa de uma mensagem simples e consistente entre todos os canais."),
    CuratedEvidence("Acessibilidade", "policy", "Passageiros que precisam de assistência requerem validação humana antes de qualquer ação."),
    CuratedEvidence("Segurança", "policy", "A segurança aeroportuária prevalece sobre metas de pontualidade em uma simulação."),
    CuratedEvidence("Handoff", "policy", "Uma decisão simulada deve terminar com perguntas objetivas para validação humana."),
    CuratedEvidence("Malha", "simulation", "Proteger a malha reduz propagação, mas pode transferir pressão para o atendimento."),
    CuratedEvidence("Rastreabilidade", "policy", "Cada decisão deve registrar evidências, hipóteses e trade-offs para revisão."),
    CuratedEvidence("Limite", "simulation", "O cenário é uma simulação baseada em dados históricos e não descreve operação ao vivo."),
]


FIXED_STRATEGIES = [
    Strategy(
        id="PROTEGER_CONEXOES",
        title="Proteger conexões",
        rationale="Priorizar voos e comunicação que reduzem o risco de perda de conexão.",
        tradeoff="Pode ampliar a pressão em voos ponto a ponto e no atendimento.",
    ),
    Strategy(
        id="PROTEGER_PONTUALIDADE",
        title="Proteger pontualidade",
        rationale="Concentrar capacidade nas operações com maior risco de propagação na malha.",
        tradeoff="Pode reduzir a margem para passageiros com conexão curta.",
    ),
    Strategy(
        id="PRIORIZAR_ATENDIMENTO",
        title="Priorizar atendimento",
        rationale="Antecipar mensagens claras e organizar a fila de validação humana.",
        tradeoff="Não elimina a limitação física de capacidade do cenário.",
    ),
]


@dataclass(frozen=True)
class ActorDefinition:
    actor_id: str
    label: str
    concern: str


ACTORS = [
    ActorDefinition("airline_ops", "Operações da companhia", "proteger a malha e limitar propagação"),
    ActorDefinition("airport_duty_manager", "Gestão aeroportuária", "preservar segurança e capacidade"),
    ActorDefinition("short_connection_passenger", "Passageiro com conexão curta", "evitar perda de conexão e falta de informação"),
    ActorDefinition("customer_service", "Atendimento ao cliente", "manter comunicação viável e consistente"),
]
