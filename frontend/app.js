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
    card.addEventListener('click', () => startPipeline(match.profession));
    card.addEventListener('keydown', e => { if (e.key === 'Enter') startPipeline(match.profession); });
    grid.appendChild(card);
  });
}

// ── Phase 2: Run Pipeline ─────────────────────────────────────────────────────

let _pollTimer = null;
let _currentRequestId = null;

async function startPipeline(profession) {
  // Show loading section
  document.getElementById('disambig-section').classList.add('hidden');
  document.getElementById('hero-section').classList.add('hidden');
  document.getElementById('loading-section').classList.remove('hidden');
  document.getElementById('loading-section').classList.add('section-fade');
  document.getElementById('loading-title').textContent = `Mapping your path to: ${profession}`;

  // Start agent step indicators cycling
  const steps = ['step-regulatory','step-education','step-certification','step-experience','step-summary'];
  let currentStep = 0;
  const stepTimer = setInterval(() => {
    if (currentStep > 0) {
      document.getElementById(steps[currentStep - 1]).classList.remove('active');
      document.getElementById(steps[currentStep - 1]).classList.add('done');
    }
    if (currentStep < steps.length) {
      document.getElementById(steps[currentStep]).classList.add('active');
      currentStep++;
    } else {
      clearInterval(stepTimer);
    }
  }, 2800);

  try {
    const res = await fetch(`${API}/api/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profession }),
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);

    const data = await res.json();
    _currentRequestId = data.request_id;

    pollForRoadmap(_currentRequestId, stepTimer);

  } catch (err) {
    clearInterval(stepTimer);
    showError('Failed to start the career analysis. Please try again.');
  }
}

async function pollForRoadmap(requestId, stepTimer) {
  const POLL_INTERVAL = 3000;
  const MAX_WAIT = 180000; // 3 minutes
  const started = Date.now();

  async function poll() {
    if (Date.now() - started > MAX_WAIT) {
      clearInterval(stepTimer);
      showError('Analysis is taking too long. Please try again.');
      return;
    }

    try {
      const res = await fetch(`${API}/api/roadmap/${requestId}`);
      if (!res.ok) {
        _pollTimer = setTimeout(poll, POLL_INTERVAL);
        return;
      }

      const doc = await res.json();

      if (doc.status === 'complete') {
        clearInterval(stepTimer);
        // Mark all steps done
        ['step-regulatory','step-education','step-certification','step-experience','step-summary']
          .forEach(id => {
            document.getElementById(id).classList.remove('active');
            document.getElementById(id).classList.add('done');
          });
        // Short delay for UX, then render
        setTimeout(() => renderRoadmap(doc), 700);

      } else if (doc.status === 'error') {
        clearInterval(stepTimer);
        showError(doc.error || 'An error occurred during analysis.');

      } else {
        // Still processing
        _pollTimer = setTimeout(poll, POLL_INTERVAL);
      }
    } catch {
      _pollTimer = setTimeout(poll, POLL_INTERVAL);
    }
  }

  poll();
}

// ── Render Roadmap ────────────────────────────────────────────────────────────

function renderRoadmap(doc) {
  const roadmap = doc.roadmap;
  const regulatory = doc.regulatory;
  const isRegulated = roadmap.is_regulated;

  // ── Header ────────────
  const header = document.getElementById('roadmap-header');
  header.innerHTML = `
    <div class="roadmap-title-block">
      <h2>${escapeHtml(roadmap.profession)}</h2>
      <p class="roadmap-duration">
        Estimated total time: <strong>${escapeHtml(roadmap.total_estimated_years || 'Varies')}</strong>
      </p>
      ${regulatory?.governing_body ? `<p style="font-size:13px;color:var(--text-muted);margin-top:4px;">
        Governing Body: <a href="${escapeHtml(regulatory.governing_body_url || '#')}" 
          target="_blank" style="color:var(--amber);text-decoration:none;">
          ${escapeHtml(regulatory.governing_body)}
        </a>
      </p>` : ''}
    </div>
    <div>
      <span class="roadmap-type-badge ${isRegulated ? 'regulated' : 'unregulated'}">
        ${isRegulated ? '🏛️ Regulated Profession' : '🌐 Unregulated Profession'}
      </span>
      ${regulatory?.protected_titles?.length ? `
        <div style="margin-top:10px;font-size:12px;color:var(--text-muted);">
          Protected titles: <strong style="color:var(--amber)">${regulatory.protected_titles.join(', ')}</strong>
        </div>` : ''}
    </div>
  `;

  // ── Steps ─────────────
  const stepsEl = document.getElementById('roadmap-steps');
  stepsEl.innerHTML = '';
  const bubbleClass = isRegulated ? 'regulated-bubble' : 'unregulated-bubble';

  roadmap.steps.forEach((step, idx) => {
    const isLast = idx === roadmap.steps.length - 1;
    const div = document.createElement('div');
    div.className = 'roadmap-step';
    div.innerHTML = `
      <div class="step-connector">
        <div class="step-bubble ${bubbleClass}">${step.step_number}</div>
        ${!isLast ? '<div class="step-line"></div>' : ''}
      </div>
      <div class="step-body">
        <div class="step-card">
          <h3>${escapeHtml(step.title)}</h3>
          <p>${escapeHtml(step.description)}</p>
          <div class="step-meta">
            <span class="step-duration">⏳ ${escapeHtml(step.estimated_duration || 'Varies')}</span>
            ${step.resources?.length ? `
              <div class="step-resources">
                ${step.resources.map(r => {
                  if (typeof r === 'object' && r.url) {
                    return `<a class="step-resource" href="${escapeHtml(r.url)}" target="_blank" style="text-decoration:underline;">${escapeHtml(r.name || r.url)}</a>`;
                  }
                  const urlMatch = String(r).match(/(https?:\/\/[^\s]+)/);
                  if (urlMatch) {
                    const url = urlMatch[1];
                    let text = String(r).replace(url, '').replace(/^[:-]\s*/, '').trim() || url;
                    return `<a class="step-resource" href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" style="text-decoration:underline; cursor:pointer;">${escapeHtml(text)}</a>`;
                  } else if (String(r).startsWith('www.')) {
                    return `<a class="step-resource" href="https://${escapeHtml(r)}" target="_blank" rel="noopener noreferrer" style="text-decoration:underline; cursor:pointer;">${escapeHtml(r)}</a>`;
                  }
                  return `<span class="step-resource">${escapeHtml(r)}</span>`;
                }).join('')}
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    `;
    stepsEl.appendChild(div);
  });

  // ── Details Grid ──────
  const grid = document.getElementById('details-grid');
  grid.innerHTML = '';

  const details = [];

  if (regulatory) {
    details.push({
      icon: '🏛️',
      title: 'Regulatory Status',
      content: regulatory.summary,
      isGoverning: true,
    });
  }
  if (doc.education) {
    let contentHtml = escapeHtml(doc.education.summary);
    if (doc.education.ontario_institutions && doc.education.ontario_institutions.length > 0) {
      contentHtml += '<div style="margin-top: 14px;"><strong>🏫 Notable Institutions:</strong><ul style="margin-top:6px; padding-left: 20px; color: var(--text-muted);">';
      doc.education.ontario_institutions.forEach(inst => {
        if (typeof inst === 'string') {
          contentHtml += `<li style="margin-bottom: 6px;">${escapeHtml(inst)}</li>`;
        } else if (inst && inst.url) {
          const safeUrl = escapeHtml(inst.url.startsWith('http') ? inst.url : `https://${inst.url}`);
          contentHtml += `
            <li style="margin-bottom: 6px;">
              <a href="${safeUrl}" target="_blank" rel="noopener noreferrer" style="color:var(--amber); text-decoration: underline; text-underline-offset: 3px; position: relative; z-index: 10;">
                ${escapeHtml(inst.name)}
              </a>
            </li>`;
        }
      });
      contentHtml += '</ul></div>';
    }
    details.push({ icon: '🎓', title: 'Education', content: contentHtml, rawHTML: true });
  }
  if (doc.certification) {
    details.push({ icon: '📋', title: 'Certifications', content: doc.certification.summary });
  }
  if (doc.experience) {
    details.push({ icon: '🏢', title: 'Experience', content: doc.experience.summary });
  }

  details.forEach(d => {
    const card = document.createElement('div');
    card.className = `detail-card ${d.isGoverning ? 'governing-body-card' : ''}`;
    const contentBody = d.rawHTML ? d.content : escapeHtml(d.content || '');
    card.innerHTML = `
      <div class="detail-icon">${d.icon}</div>
      <h4>${escapeHtml(d.title)}</h4>
      <div class="detail-body">${contentBody}</div>
    `;
    grid.appendChild(card);
  });

  // ── Key Links ─────────
  if (roadmap.key_links?.length) {
    const linksSection = document.getElementById('key-links-section');
    const linksList = document.getElementById('key-links-list');
    linksList.innerHTML = '';
    roadmap.key_links.forEach(link => {
      const a = document.createElement('a');
      a.className = 'key-link';
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      
      const urlMatch = String(link).match(/(https?:\/\/[^\s]+)/);
      if (urlMatch) {
        a.href = urlMatch[1];
        a.textContent = String(link).replace(urlMatch[1], '').replace(/^[:-]\s*/, '').trim() || urlMatch[1];
      } else if (String(link).startsWith('www.')) {
        a.href = `https://${link}`;
        a.textContent = link;
      } else {
        a.href = `https://www.google.com/search?q=${encodeURIComponent('Ontario ' + link)}`;
        a.textContent = link + ' 🔍'; // Add search icon so users know what it'll do
      }
      linksList.appendChild(a);
    });
    linksSection.classList.remove('hidden');
  }

  // ── Notes ─────────────
  if (roadmap.important_notes?.length) {
    const notesSection = document.getElementById('notes-section');
    const notesList = document.getElementById('notes-list');
    notesList.innerHTML = '';
    roadmap.important_notes.forEach(note => {
      const li = document.createElement('li');
      li.textContent = note;
      notesList.appendChild(li);
    });
    notesSection.classList.remove('hidden');
  }

  // ── Show section ──────
  document.getElementById('loading-section').classList.add('hidden');
  document.getElementById('roadmap-section').classList.remove('hidden');
  document.getElementById('roadmap-section').classList.add('section-fade');
  window.scrollTo({ top: 0, behavior: 'smooth' });
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
