/* ─────────────────────────────────────────────────────────────────────────────
   Ontario Career Path Engine — Frontend Logic
   Flow:
   1. User types → POST /api/disambiguate → show profession options
   2. User clicks a card → POST /api/search → get request_id
   3. Poll GET /api/roadmap/{request_id} until status=complete
   4. Render regulated or unregulated roadmap
───────────────────────────────────────────────────────────────────────────── */

const API = '';   // Empty = same origin. Change to 'http://localhost:8000' if running frontend separately.

// ── Section helpers ───────────────────────────────────────────────────────────

function showSection(id) {
  ['hero-section','disambig-section','loading-section','roadmap-section','error-section']
    .forEach(s => {
      const el = document.getElementById(s);
      if (s === id) {
        el.classList.remove('hidden');
      } else {
        // Keep hero visible underneath search
        if (s === 'hero-section' && id !== 'hero-section') {
          // Hide hero when we show other major sections
          if (['roadmap-section','error-section'].includes(id)) {
            el.classList.add('hidden');
          }
        } else {
          el.classList.add('hidden');
        }
      }
    });
}

function setSearchLoading(isLoading) {
  const btn = document.getElementById('search-btn');
  const btnText = document.getElementById('btn-text');
  const btnLoader = document.getElementById('btn-loader');
  const input = document.getElementById('profession-input');

  btn.disabled = isLoading;
  input.disabled = isLoading;
  if (isLoading) {
    btnText.classList.add('hidden');
    btnLoader.classList.remove('hidden');
  } else {
    btnText.classList.remove('hidden');
    btnLoader.classList.add('hidden');
  }
}

function showInputError(msg) {
  const el = document.getElementById('input-error');
  el.textContent = msg;
  el.classList.remove('hidden');
}

function clearInputError() {
  document.getElementById('input-error').classList.add('hidden');
}

// ── Reset ─────────────────────────────────────────────────────────────────────

function resetToSearch() {
  document.getElementById('profession-input').value = '';
  document.getElementById('profession-input').disabled = false;
  document.getElementById('search-btn').disabled = false;
  clearInputError();
  showSection('hero-section');
  document.getElementById('hero-section').classList.remove('hidden');
  document.getElementById('disambig-section').classList.add('hidden');
  document.getElementById('loading-section').classList.add('hidden');
  document.getElementById('roadmap-section').classList.add('hidden');
  document.getElementById('error-section').classList.add('hidden');
  setSearchLoading(false);

  // Reset agent progress dots
  ['step-regulatory','step-education','step-certification','step-experience','step-summary']
    .forEach(id => {
      const el = document.getElementById(id);
      el.classList.remove('active','done');
    });

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── Phase 1: Disambiguation ───────────────────────────────────────────────────

async function handleSearch() {
  const query = document.getElementById('profession-input').value.trim();
  clearInputError();

  if (!query) {
    showInputError('Please enter a profession to search.');
    return;
  }

  setSearchLoading(true);

  try {
    const res = await fetch(`${API}/api/disambiguate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    const data = await res.json();

    if (data.error || !data.matches || data.matches.length === 0) {
      showInputError(data.error || 'No matching professions found. Try a more specific term.');
      setSearchLoading(false);
      return;
    }

    renderDisambigCards(data.matches);
    setSearchLoading(false);
    showSection('disambig-section');
    document.getElementById('hero-section').classList.remove('hidden');
    document.getElementById('disambig-section').classList.remove('hidden');

  } catch (err) {
    showInputError('Could not connect to the server. Is the backend running?');
    setSearchLoading(false);
  }
}

function renderDisambigCards(matches) {
  const grid = document.getElementById('disambig-cards');
  grid.innerHTML = '';

  matches.forEach(match => {
    const isRegulated = match.is_regulated;
    const badgeText = isRegulated ? `Regulated: ${match.regulatory_bucket}` : "Unregulated Free Market";
    const wageBadge = match.median_wage
      ? `<span class="wage-badge">💰 Ontario median: <strong>${escapeHtml(match.median_wage)}</strong></span>`
      : '';
    const card = document.createElement('div');
    card.className = 'disambig-card';
    card.setAttribute('role', 'button');
    card.setAttribute('tabindex', '0');
    card.innerHTML = `
      <span class="card-badge ${isRegulated ? 'badge-regulated' : 'badge-unregulated'}">
        ${escapeHtml(badgeText)}
      </span>
      <div class="card-title">${escapeHtml(match.profession)}</div>
      <div class="card-note">${escapeHtml(match.note)}</div>
      ${wageBadge}
      <span class="card-arrow">→</span>
    `;
    card.addEventListener('click', () => startPipeline(match.profession, match.is_regulated));
    card.addEventListener('keydown', e => { if (e.key === 'Enter') startPipeline(match.profession, match.is_regulated); });
    grid.appendChild(card);
  });
}

// ── Phase 2: Run Pipeline ─────────────────────────────────────────────────────

// ── Phase 2: Dynamic Pipeline Orchestrator ────────────────────────────────────

const ACTIVE_AGENTS = [
  { id: 'regulatory', title: 'Regulatory Status', endpoint: '/api/agent/regulatory', icon: '🏛️', completed: false, data: null },
  { id: 'education', title: 'Education Requirements', endpoint: '/api/agent/education', icon: '🎓', completed: false, data: null },
  { id: 'certification', title: 'Certifications & Exams', endpoint: '/api/agent/certification', icon: '📋', completed: false, data: null },
  { id: 'experience', title: 'Experience Requirements', endpoint: '/api/agent/experience', icon: '🏢', completed: false, data: null }
];

let currentProfession = "";
let currentIsRegulated = false;

function startPipeline(profession, isRegulated) {
  currentProfession = profession;
  currentIsRegulated = isRegulated;

  // Reset agents state
  ACTIVE_AGENTS.forEach(a => {
    a.completed = false;
    a.data = null;
  });

  // Switch sections
  document.getElementById('disambig-section').classList.add('hidden');
  document.getElementById('hero-section').classList.add('hidden');
  document.getElementById('roadmap-section').classList.remove('hidden');
  document.getElementById('roadmap-section').classList.add('section-fade');

  // Set Header
  const header = document.getElementById('roadmap-header');
  header.innerHTML = `
    <div class="roadmap-title-block">
      <h2>${escapeHtml(profession)}</h2>
    </div>
    <div>
      <span class="roadmap-type-badge ${isRegulated ? 'regulated' : 'unregulated'}">
        ${isRegulated ? '🏛️ Regulated Profession' : '🌐 Unregulated Profession'}
      </span>
    </div>
  `;

  // Render Agent Cards Dashboard
  const container = document.getElementById('agent-cards-container');
  container.innerHTML = '';

  ACTIVE_AGENTS.forEach(agent => {
    const card = document.createElement('div');
    card.className = 'detail-card';
    card.id = `agent-card-${agent.id}`;
    card.innerHTML = `
      <div class="detail-icon">${agent.icon}</div>
      <h4>${agent.title}</h4>
      <div id="agent-content-${agent.id}" class="detail-body" style="margin-bottom: 15px;">Pending analysis...</div>
      <button id="btn-${agent.id}" class="btn-primary" style="padding: 6px 12px; font-size: 13px;" onclick="triggerAgent('${agent.id}')">Analyze</button>
    `;
    container.appendChild(card);
  });

  // Reset Final Roadmap Section
  const compileBtn = document.getElementById('btn-compile-roadmap');
  compileBtn.disabled = true;
  compileBtn.style.display = 'inline-block';
  compileBtn.textContent = 'Compile Final Roadmap';
  compileBtn.onclick = compileFinalRoadmap;
  
  document.getElementById('btn-download-pdf').classList.add('hidden');
  document.getElementById('final-roadmap-content').innerHTML = '';
}

async function triggerAgent(agentId) {
  const agent = ACTIVE_AGENTS.find(a => a.id === agentId);
  const btn = document.getElementById(`btn-${agentId}`);
  const content = document.getElementById(`agent-content-${agentId}`);

  btn.disabled = true;
  btn.textContent = 'Analyzing...';
  
  try {
    const payload = { profession: currentProfession };
    if (agentId !== 'regulatory') {
      payload.is_regulated = currentIsRegulated;
    }

    const res = await fetch(`${API}${agent.endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error('API Error');

    const data = await res.json();
    agent.data = data;
    agent.completed = true;

    content.innerHTML = escapeHtml(data.summary || 'Analysis complete.');
    btn.style.display = 'none';

    checkAllAgentsComplete();

  } catch (err) {
    btn.disabled = false;
    btn.textContent = 'Retry';
    content.innerHTML = '<span style="color:var(--error);">Failed. Please try again.</span>';
  }
}

function checkAllAgentsComplete() {
  const allDone = ACTIVE_AGENTS.every(a => a.completed);
  if (allDone) {
    document.getElementById('btn-compile-roadmap').disabled = false;
  }
}

async function compileFinalRoadmap() {
  const compileBtn = document.getElementById('btn-compile-roadmap');
  compileBtn.disabled = true;
  compileBtn.textContent = 'Compiling...';

  try {
    const payload = {
      profession: currentProfession,
      regulatory: ACTIVE_AGENTS.find(a => a.id === 'regulatory').data,
      education: ACTIVE_AGENTS.find(a => a.id === 'education').data,
      certification: ACTIVE_AGENTS.find(a => a.id === 'certification').data,
      experience: ACTIVE_AGENTS.find(a => a.id === 'experience').data
    };

    const res = await fetch(`${API}/api/agent/summarize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error('API Error');
    const roadmap = await res.json();

    renderFinalRoadmap(roadmap);
    compileBtn.style.display = 'none';
    document.getElementById('btn-download-pdf').classList.remove('hidden');

  } catch (err) {
    compileBtn.disabled = false;
    compileBtn.textContent = 'Retry Compile';
    alert('Failed to compile roadmap.');
  }
}

function renderFinalRoadmap(roadmap) {
  const container = document.getElementById('final-roadmap-content');
  let html = `<div style="padding: 20px; background: white; border-radius: 8px; border: 1px solid var(--border-color);">
    <h3 style="margin-bottom: 15px;">Step-by-step Roadmap</h3><div class="roadmap-steps">`;
  
  roadmap.steps.forEach((step, idx) => {
    html += `
      <div class="roadmap-step">
        <div class="step-connector">
          <div class="step-bubble ${currentIsRegulated ? 'regulated-bubble' : 'unregulated-bubble'}">${step.step_number}</div>
          ${idx < roadmap.steps.length - 1 ? '<div class="step-line"></div>' : ''}
        </div>
        <div class="step-body">
          <div class="step-card">
            <h4>${escapeHtml(step.title)}</h4>
            <p>${escapeHtml(step.description)}</p>
            <div class="step-meta">
              <span class="step-duration">⏳ ${escapeHtml(step.estimated_duration || 'Varies')}</span>
            </div>
          </div>
        </div>
      </div>
    `;
  });
  html += `</div></div>`;
  container.innerHTML = html;
}

function downloadPDF() {
  const element = document.getElementById('final-roadmap-content');
  html2pdf().from(element).save('roadmap.pdf');
}

// ── Error ─────────────────────────────────────────────────────────────────────

function showError(msg) {
  document.getElementById('loading-section').classList.add('hidden');
  document.getElementById('disambig-section').classList.add('hidden');
  document.getElementById('hero-section').classList.add('hidden');
  document.getElementById('error-message').textContent = msg;
  document.getElementById('error-section').classList.remove('hidden');
  document.getElementById('error-section').classList.add('section-fade');
}

// ── Utility ───────────────────────────────────────────────────────────────────

function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ── Keyboard shortcut: Enter key ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('profession-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') handleSearch();
  });
});
