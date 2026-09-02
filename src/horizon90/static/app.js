const form = document.querySelector('#scenario-form');
const message = document.querySelector('#form-message');
const decisionButton = document.querySelector('#decision-button');
let activeRun = null;
let selectedStrategy = null;

const labels = { real: 'real', fallback: 'fallback', unavailable: 'indisponível' };

function setMessage(text, tone = '') {
  message.textContent = text;
  message.className = `form-message ${tone}`;
}

function readScenario() {
  return {
    airport_iata: document.querySelector('#airport_iata').value.toUpperCase().trim(),
    start_at: document.querySelector('#start_at').value,
    duration_minutes: Number(document.querySelector('#duration_minutes').value),
    capacity_reduction_pct: Number(document.querySelector('#capacity_reduction_pct').value),
    confirmed: document.querySelector('#confirmed').checked,
  };
}

function renderStatus(status) {
  Object.entries(status).forEach(([key, value]) => {
    const item = document.querySelector(`[data-key="${key}"]`);
    item.dataset.status = value;
    item.querySelector('b').textContent = labels[value];
  });
}

function renderExposure(exposure) {
  document.querySelector('#metric-flights').textContent = exposure.affected_flights;
  document.querySelector('#metric-bookings').textContent = exposure.affected_bookings;
  document.querySelector('#metric-capacity').textContent = exposure.affected_capacity;
  document.querySelector('#exposure-source').textContent = exposure.source === 'tidb' ? 'TiDB real' : 'fallback local';
}

function renderStrategies(strategies) {
  const list = document.querySelector('#strategy-list');
  list.innerHTML = '';
  strategies.forEach((strategy, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'strategy';
    button.dataset.id = strategy.id;
    button.innerHTML = `<span>${String(index + 1).padStart(2, '0')}</span><div><strong>${strategy.title}</strong><p>${strategy.rationale}</p><small>Trade-off: ${strategy.tradeoff}</small></div><em>Selecionar</em>`;
    button.addEventListener('click', () => {
      selectedStrategy = strategy.id;
      document.querySelectorAll('.strategy').forEach((item) => item.classList.toggle('selected', item === button));
      decisionButton.disabled = false;
      document.querySelector('#decision-content').textContent = `Estratégia selecionada: ${strategy.title}. Revise o pacote antes de qualquer ação.`;
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
    article.innerHTML = `<header><strong>${reaction.actor_label}</strong><span>${reaction.availability === 'real' ? 'ativo' : 'indisponível'}</span></header><p>${reaction.likely_reaction}</p><dl><div><dt>Objeção</dt><dd>${reaction.objection}</dd></div><div><dt>Validar</dt><dd>${reaction.validation_question}</dd></div></dl>`;
    list.appendChild(article);
  });
}

function renderEvidence(evidence) {
  const list = document.querySelector('#evidence-list');
  list.innerHTML = '';
  evidence.forEach((item) => {
    const li = document.createElement('li');
    li.innerHTML = `<span>${item.source_label}</span>${item.content}`;
    list.appendChild(li);
  });
}

function renderDecision(pack) {
  const content = document.querySelector('#decision-content');
  content.innerHTML = `<strong>${pack.recommended_action}</strong><p>${pack.tradeoffs.join(' ')}</p><p class="archive">Replay: ${pack.archive_status === 'archived' ? pack.archive_key : 'não arquivado'}</p><p>Validação humana: ${pack.human_validation_questions.join(' · ')}</p>`;
}

async function runScenario(event) {
  event.preventDefault();
  selectedStrategy = null;
  decisionButton.disabled = true;
  document.querySelector('#run-button').disabled = true;
  setMessage('Executando ensaio…');
  try {
    const response = await fetch('/api/runs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(readScenario()) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail?.message || payload.message || 'Não foi possível iniciar o ensaio.');
    activeRun = payload.run_id;
    renderStatus(payload.integration_status);
    renderExposure(payload.exposure);
    renderStrategies(payload.strategies);
    renderReactions(payload.reactions);
    renderEvidence(payload.evidence);
    document.querySelector('#run-state').textContent = `Execução ${activeRun.slice(0, 8)}`;
    setMessage('Ensaio concluído. Escolha uma estratégia.', 'success');
  } catch (error) {
    setMessage(error.message, 'error');
  } finally {
    document.querySelector('#run-button').disabled = false;
  }
}

async function createDecision() {
  if (!activeRun || !selectedStrategy) return;
  decisionButton.disabled = true;
  decisionButton.textContent = 'Gerando pacote…';
  try {
    const response = await fetch(`/api/runs/${activeRun}/decision`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ strategy_id: selectedStrategy }) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail?.message || 'Não foi possível gerar o pacote.');
    renderDecision(payload);
  } catch (error) {
    document.querySelector('#decision-content').textContent = error.message;
  } finally {
    decisionButton.disabled = false;
    decisionButton.textContent = 'Gerar pacote de decisão';
  }
}

async function loadSeed() {
  const response = await fetch('/api/seed');
  const seed = await response.json();
  document.querySelector('#airport_iata').value = seed.airport_iata;
  document.querySelector('#start_at').value = seed.start_at.slice(0, 16);
  document.querySelector('#duration_minutes').value = seed.duration_minutes;
  document.querySelector('#capacity_reduction_pct').value = seed.capacity_reduction_pct;
  document.querySelector('#confirmed').checked = seed.confirmed;
}

form.addEventListener('submit', runScenario);
decisionButton.addEventListener('click', createDecision);
loadSeed().catch(() => setMessage('Cenário-semente indisponível.', 'error'));
