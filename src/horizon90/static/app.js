const form = document.querySelector('#scenario-form');
const message = document.querySelector('#form-message');
const decisionButton = document.querySelector('#decision-button');
const durationInput = document.querySelector('#duration_minutes');
const capacityInput = document.querySelector('#capacity_reduction_pct');
const capacityRange = document.querySelector('#capacity_range');
const capacityDisplay = document.querySelector('#capacity-display');
const impactNote = document.querySelector('#impact-note');
let activeRun = null;
let selectedStrategy = null;

const labels = { real: 'verificado', fallback: 'alternativo', unavailable: 'indisponível' };
const actionWindowLabels = { agora: 'Agora', '15_min': 'Próximos 15 min', '30_min': 'Até 30 min', fim_da_janela: 'Fim da janela' };

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[character]);
}

function formatNumber(value) {
  return new Intl.NumberFormat('pt-BR').format(Number(value));
}

function setMessage(text, tone = '') {
  message.textContent = text;
  message.className = `form-message ${tone}`;
}

function setWorkflow(state) {
  const order = ['configure', 'running', 'compare', 'decide'];
  const current = order.indexOf(state);
  document.querySelectorAll('.workflow-step').forEach((step, index) => {
    step.classList.toggle('active', index === current);
    step.classList.toggle('complete', index < current);
  });
}

function describeImpact(value) {
  if (value <= 20) return 'representa um cenário de atenção controlada.';
  if (value <= 40) return 'representa um cenário de estresse moderado.';
  if (value <= 60) return 'representa um cenário de estresse elevado.';
  return 'representa um cenário crítico de capacidade.';
}

function syncCapacity(value) {
  const parsed = Math.min(80, Math.max(10, Number(value) || 10));
  capacityInput.value = parsed;
  capacityRange.value = parsed;
  capacityDisplay.textContent = `${parsed}%`;
  impactNote.textContent = `${parsed}% ${describeImpact(parsed)}`;
}

function syncDurationPresets() {
  const duration = Number(durationInput.value);
  document.querySelectorAll('[data-duration]').forEach((button) => button.classList.toggle('selected', Number(button.dataset.duration) === duration));
}

function readScenario() {
  return {
    airport_iata: document.querySelector('#airport_iata').value.toUpperCase().trim(),
    start_at: document.querySelector('#start_at').value,
    duration_minutes: Number(durationInput.value),
    capacity_reduction_pct: Number(capacityInput.value),
    confirmed: document.querySelector('#confirmed').checked,
  };
}

function renderStatus(status) {
  Object.entries(status).forEach(([key, value]) => {
    const item = document.querySelector(`[data-key="${key}"]`);
    if (!item) return;
    item.dataset.status = value;
    item.querySelector('b').textContent = key === 'archive' && value === 'real' ? 'pronto' : (labels[value] || value);
  });
}

function renderExposure(exposure) {
  document.querySelector('#metric-flights').textContent = formatNumber(exposure.affected_flights);
  document.querySelector('#metric-bookings').textContent = formatNumber(exposure.affected_bookings);
  document.querySelector('#metric-capacity').textContent = formatNumber(exposure.affected_capacity);
  document.querySelector('#exposure-source').textContent = exposure.source === 'tidb' ? 'Dados TiDB verificados' : 'Dados locais alternativos';
}

function renderStrategies(strategies) {
  const list = document.querySelector('#strategy-list');
  list.innerHTML = '';
  strategies.forEach((strategy, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'strategy';
    button.dataset.id = strategy.id;
    button.setAttribute('aria-pressed', 'false');
    button.innerHTML = `<span class="strategy-index">${String(index + 1).padStart(2, '0')}</span><div class="strategy-copy"><strong>${escapeHtml(strategy.title)}</strong><p>${escapeHtml(strategy.rationale)}</p><small>Trade-off: ${escapeHtml(strategy.tradeoff)}</small></div><span class="strategy-action">Selecionar <i aria-hidden="true">→</i></span>`;
    button.addEventListener('click', () => {
      selectedStrategy = strategy.id;
      document.querySelectorAll('.strategy').forEach((item) => {
        const isSelected = item === button;
        item.classList.toggle('selected', isSelected);
        item.setAttribute('aria-pressed', String(isSelected));
      });
      decisionButton.disabled = false;
      document.querySelector('#strategy-state').textContent = 'Estratégia selecionada';
      document.querySelector('#decision-state').textContent = 'Pronto para gerar';
      document.querySelector('#decision-content').textContent = `Estratégia selecionada: ${strategy.title}. Gere a folha de resposta para revisar próximos passos, trade-offs e validações humanas.`;
      setWorkflow('decide');
    });
    list.appendChild(button);
  });
}

function renderReactions(reactions) {
  const list = document.querySelector('#reaction-list');
  list.innerHTML = '';
  reactions.forEach((reaction) => {
    const article = document.createElement('article');
    article.className = 'reaction';
    article.dataset.availability = reaction.availability;
    const availability = reaction.availability === 'real' ? 'analisado' : 'indisponível';
    article.innerHTML = `<header><strong>${escapeHtml(reaction.actor_label)}</strong><span>${availability}</span></header><p>${escapeHtml(reaction.likely_reaction)}</p><dl><div><dt>Possível objeção</dt><dd>${escapeHtml(reaction.objection)}</dd></div><div><dt>Validar antes de agir</dt><dd>${escapeHtml(reaction.validation_question)}</dd></div></dl>`;
    list.appendChild(article);
  });
}

function renderEvidence(evidence) {
  const list = document.querySelector('#evidence-list');
  list.innerHTML = '';
  evidence.forEach((item) => {
    const li = document.createElement('li');
    li.innerHTML = `<span>${escapeHtml(item.source_label)}</span>${escapeHtml(item.content)}`;
    list.appendChild(li);
  });
}

function renderDecision(pack) {
  const content = document.querySelector('#decision-content');
  const actions = (pack.action_plan || []).map((item) => `<li><span>${escapeHtml(actionWindowLabels[item.time_window] || item.time_window)}</span><div><strong>${escapeHtml(item.owner)}</strong><p>${escapeHtml(item.action)}</p><small>Sinal de avanço: ${escapeHtml(item.success_signal)}</small></div></li>`).join('');
  const impacts = (pack.impact_watch || []).map((impact) => `<span>${escapeHtml(impact)}</span>`).join('');
  const archive = pack.archive_status === 'archived'
    ? `Registro local salvo nesta máquina: ${escapeHtml(pack.archive_key || 'arquivo disponível')}.`
    : 'Registro local não pôde ser gravado nesta execução.';
  content.innerHTML = `<div class="decision-recommendation"><strong>${escapeHtml(pack.recommended_action)}</strong><p>${pack.tradeoffs.map(escapeHtml).join(' ')}</p></div><div class="review-gate"><span>PRÓXIMA REAVALIAÇÃO</span><strong>em ${escapeHtml(pack.next_review_minutes)} min</strong></div><section class="action-plan"><h4>Próximas ações sugeridas</h4><ol>${actions || '<li class="empty">O plano temporal não está disponível.</li>'}</ol></section><section class="impact-watch"><h4>Impactos a acompanhar</h4><div>${impacts || '<span>Revisar impactos com a equipe</span>'}</div></section><p class="archive">${archive}</p><p class="validation-label">Validação humana necessária</p><ul class="validation-list">${pack.human_validation_questions.map((question) => `<li>${escapeHtml(question)}</li>`).join('')}</ul>`;
  document.querySelector('#decision-state').textContent = 'Pacote gerado';
}

function resetRunOutputs() {
  document.querySelector('#strategy-state').textContent = 'Calculando opções';
  document.querySelector('#decision-state').textContent = 'Aguardando estratégia';
  document.querySelector('#decision-content').textContent = 'A simulação está sendo atualizada. Compare as opções antes de preparar uma decisão.';
}

async function runScenario(event) {
  event.preventDefault();
  selectedStrategy = null;
  decisionButton.disabled = true;
  document.querySelector('#run-button').disabled = true;
  document.querySelector('#run-button span').textContent = 'Simulando cenário';
  document.querySelector('#run-state').textContent = 'Calculando exposição';
  document.querySelector('#results-title').textContent = 'Simulação em andamento';
  document.querySelector('#results-caption').textContent = 'Consultando os dados históricos e organizando as opções de resposta.';
  resetRunOutputs();
  setWorkflow('running');
  setMessage('Simulação em andamento. Os resultados aparecerão nesta página.', 'loading');
  try {
    const response = await fetch('/api/runs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(readScenario()) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail?.message || payload.message || 'Não foi possível executar a simulação. Revise os parâmetros e tente novamente.');
    activeRun = payload.run_id;
    renderStatus(payload.integration_status);
    renderExposure(payload.exposure);
    renderStrategies(payload.strategies);
    renderReactions(payload.reactions);
    renderEvidence(payload.evidence);
    document.querySelector('#run-state').textContent = `Cenário ${activeRun.slice(0, 8)}`;
    document.querySelector('#results-title').textContent = 'Resultados prontos para comparação';
    document.querySelector('#results-caption').textContent = 'Analise a dimensão do impacto, compare as opções de resposta e selecione uma para montar o pacote revisável.';
    document.querySelector('#strategy-state').textContent = 'Escolha uma resposta';
    setWorkflow('compare');
    setMessage('Simulação concluída. Escolha uma opção de resposta para continuar.', 'success');
  } catch (error) {
    document.querySelector('#run-state').textContent = 'Revisar parâmetros';
    document.querySelector('#results-title').textContent = 'Não foi possível concluir';
    document.querySelector('#results-caption').textContent = 'A simulação não foi executada. Revise os controles à esquerda e tente novamente.';
    setWorkflow('configure');
    setMessage(error.message, 'error');
  } finally {
    document.querySelector('#run-button').disabled = false;
    document.querySelector('#run-button span').textContent = 'Executar simulação';
  }
}

async function createDecision() {
  if (!activeRun || !selectedStrategy) return;
  decisionButton.disabled = true;
  decisionButton.querySelector('span').textContent = 'Gerando folha';
  document.querySelector('#decision-state').textContent = 'Organizando recomendação';
  try {
    const response = await fetch(`/api/runs/${activeRun}/decision`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ strategy_id: selectedStrategy }) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail?.message || 'Não foi possível gerar a folha de resposta.');
    renderDecision(payload);
    setMessage('Folha de resposta gerada para revisão humana.', 'success');
  } catch (error) {
    document.querySelector('#decision-content').textContent = error.message;
    document.querySelector('#decision-state').textContent = 'Tentar novamente';
  } finally {
    decisionButton.disabled = false;
    decisionButton.querySelector('span').textContent = 'Gerar folha de resposta';
  }
}

async function loadSeed() {
  const response = await fetch('/api/seed');
  if (!response.ok) throw new Error('Cenário-semente indisponível.');
  const seed = await response.json();
  document.querySelector('#airport_iata').value = seed.airport_iata;
  document.querySelector('#start_at').value = seed.start_at.slice(0, 16);
  durationInput.value = seed.duration_minutes;
  syncDurationPresets();
  syncCapacity(seed.capacity_reduction_pct);
  document.querySelector('#confirmed').checked = seed.confirmed;
}

form.addEventListener('submit', runScenario);
decisionButton.addEventListener('click', createDecision);
capacityRange.addEventListener('input', (event) => syncCapacity(event.target.value));
capacityInput.addEventListener('input', (event) => syncCapacity(event.target.value));
durationInput.addEventListener('input', syncDurationPresets);
document.querySelectorAll('[data-duration]').forEach((button) => button.addEventListener('click', () => {
  durationInput.value = button.dataset.duration;
  syncDurationPresets();
  durationInput.focus();
}));
loadSeed().catch((error) => setMessage(error.message, 'error'));
