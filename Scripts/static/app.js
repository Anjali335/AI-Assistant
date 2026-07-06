/* ─── State ──────────────────────────────────────────────────────────────────── */
const messagesEl  = document.getElementById('messages');
const inputEl     = document.getElementById('msg-input');
const sendBtn     = document.getElementById('send-btn');
const stopBtn     = document.getElementById('stop-btn');
const menuBtn     = document.getElementById('menu-btn');
const sidebar     = document.getElementById('sidebar');
const statusDot   = document.getElementById('status-dot');
const statusText  = document.getElementById('status-text');

let isBusy             = false;
let sidebarOpen        = false;
let currentAbortController = null;

/* ─── Dark Mode Theme Setup ─────────────────────────────────────────────────── */
let currentTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', currentTheme);

const themeToggle = document.getElementById('theme-toggle');
if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem('theme', currentTheme);
  });
}

/* ─── Aesthetic Presets Palette Setup ────────────────────────────────────────── */
let currentPreset = localStorage.getItem('theme-preset') || 'indigo';
document.documentElement.setAttribute('data-preset', currentPreset);

document.querySelectorAll('.theme-preset-btn').forEach(btn => {
  if (btn.dataset.preset === currentPreset) btn.classList.add('active');
  else btn.classList.remove('active');
  
  btn.addEventListener('click', () => {
    document.querySelectorAll('.theme-preset-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentPreset = btn.dataset.preset;
    document.documentElement.setAttribute('data-preset', currentPreset);
    localStorage.setItem('theme-preset', currentPreset);
  });
});



/* ─── Status Poll ──────────────────────────────────────────────────────────── */
async function checkStatus() {
  try {
    const res  = await fetch('/api/status');
    const data = await res.json();
    if (data.loading_complete) {
      const parts = [];
      if (data.ml_model_loaded)   parts.push('Vector Search');
      if (data.gemini_configured) parts.push('Gemini AI');
      if (!parts.length)          parts.push('Keyword Search');

      statusDot.className  = 'status-dot online';
      statusText.textContent = `Online · ${parts.join(' + ')}`;
    } else {
      statusDot.className  = 'status-dot';
      statusText.textContent = `Loading data (${data.notices_loaded} notices)...`;
      setTimeout(checkStatus, 2500);
    }
  } catch {
    statusDot.className  = 'status-dot error';
    statusText.textContent = 'Connection error';
    setTimeout(checkStatus, 5000);
  }
}
checkStatus();

/* ─── Sidebar Toggle ───────────────────────────────────────────────────────── */
menuBtn.addEventListener('click', () => {
  sidebarOpen = !sidebarOpen;
  sidebar.classList.toggle('open', sidebarOpen);
});
document.addEventListener('click', e => {
  if (sidebarOpen && !sidebar.contains(e.target) && e.target !== menuBtn) {
    sidebarOpen = false;
    sidebar.classList.remove('open');
  }
});

/* ─── Quick-topic chips in sidebar ────────────────────────────────────────── */
document.querySelectorAll('.nav-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    const q = chip.dataset.query;
    if (q) {
      inputEl.value = q;
      sendMessage();
      // Close sidebar on mobile
      sidebarOpen = false;
      sidebar.classList.remove('open');
    }
  });
});

/* ─── Welcome Screen ───────────────────────────────────────────────────────── */
function renderWelcome() {
  const suggestions = [
    { title: 'Placements', query: 'latest placement drives', icon: '💼', desc: 'Job drives, recruitments & companies' },
    { title: 'AKTU Exams', query: 'AKTU exam schedule', icon: '📋', desc: 'Schedules, forms & date sheets' },
    { title: 'BTEUP Updates', query: 'BTEUP notices', icon: '📄', desc: 'Polytechnic exam & result notices' },
    { title: 'Admissions', query: 'admission process and requirements', icon: '🎯', desc: 'Fees, registration & eligibility' },
    { title: 'MSU Updates', query: 'MSU exam results', icon: '🏛️', desc: 'Maa Shakumbhari Univ notices' },
    { title: 'Campus Events', query: 'campus events and news', icon: '📅', desc: 'TVARAN cultural fest & news' }
  ];

  const block = document.createElement('div');
  block.className = 'welcome-block';
  block.id = 'welcome-block';
  block.innerHTML = `
    <div class="welcome-hero">
      <span class="welcome-emoji">🎓</span>
      <h1 class="welcome-heading">Welcome to DBGI Assistant</h1>
      <p class="welcome-sub">Explore notices, placements, exams, and campus life immediately. Click any topic below to start.</p>
    </div>
    <div class="welcome-grid">
      ${suggestions.map(s => `
        <button class="welcome-card" data-query="${s.query}">
          <div class="welcome-card-header">
            <span class="welcome-card-icon">${s.icon}</span>
            <span class="welcome-card-arrow">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"></line>
                <polyline points="12 5 19 12 12 19"></polyline>
              </svg>
            </span>
          </div>
          <h3 class="welcome-card-title">${s.title}</h3>
          <p class="welcome-card-desc">${s.desc}</p>
        </button>
      `).join('')}
    </div>
    
    <div class="announcements-panel">
      <div class="announcements-header">
        <span class="announcements-title-icon">📢</span>
        <h2 class="announcements-panel-title">Latest Announcements & Highlights</h2>
        <span class="announcements-badge">Live Feed</span>
      </div>
      <div class="announcements-feed" id="announcements-feed">
        <div class="announcement-skeleton">Loading latest updates...</div>
        <div class="announcement-skeleton">Loading latest updates...</div>
      </div>
    </div>
  `;

  block.querySelectorAll('.welcome-card').forEach(card => {
    card.addEventListener('click', () => {
      const q = card.dataset.query;
      inputEl.value = q;
      sendMessage();
    });
  });

  messagesEl.appendChild(block);

  // Asynchronously fetch latest announcements
  fetch('/api/notices/latest')
    .then(res => res.json())
    .then(items => {
      const feedEl = block.querySelector('#announcements-feed');
      if (!feedEl) return;
      if (!items || items.length === 0) {
        feedEl.innerHTML = '<div class="announcement-empty">No recent notifications found.</div>';
        return;
      }
      
      feedEl.innerHTML = items.map(item => {
        const isPdf = item.url && item.url.toLowerCase().endsWith('.pdf');
        const catClass = item.category.toLowerCase().replace(/[^a-z0-9]/g, '');
        return `
          <div class="announcement-item">
            <div class="announcement-meta">
              <span class="announcement-date">📅 ${item.date}</span>
              <span class="announcement-category badge-${catClass}">${item.category}</span>
              ${isPdf ? '<span class="pdf-tag">PDF</span>' : ''}
            </div>
            <h4 class="announcement-title">${item.title}</h4>
            <div class="announcement-actions">
              <button class="announcement-query-btn" data-query="Can you explain the details of the notice: ${item.title}?">Ask AI</button>
              ${item.url ? `<a href="${item.url}" target="_blank" class="announcement-link">View original →</a>` : ''}
            </div>
          </div>
        `;
      }).join('');
      
      // Bind query triggers
      feedEl.querySelectorAll('.announcement-query-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const q = btn.dataset.query;
          inputEl.value = q;
          sendMessage();
        });
      });
    })
    .catch(err => {
      console.error('Error fetching announcements:', err);
      const feedEl = block.querySelector('#announcements-feed');
      if (feedEl) {
        feedEl.innerHTML = '<div class="announcement-error">Failed to load live announcements.</div>';
      }
    });
}
renderWelcome();

/* ─── Clear Chat Action ─────────────────────────────────────────────────────── */
const clearChatBtn = document.getElementById('clear-chat');
if (clearChatBtn) {
  clearChatBtn.addEventListener('click', () => {
    messagesEl.style.opacity = '0';
    messagesEl.style.transform = 'translateY(12px)';
    setTimeout(() => {
      messagesEl.innerHTML = '';
      messagesEl.style.opacity = '1';
      messagesEl.style.transform = 'none';
      renderWelcome();
    }, 300);
  });
}

/* ─── Floating Scroll Button ────────────────────────────────────────────────── */
const scrollBtn = document.getElementById('scroll-bottom-btn');
if (scrollBtn) {
  messagesEl.addEventListener('scroll', () => {
    const isScrolledUp = messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight > 220;
    if (isScrolledUp) {
      scrollBtn.classList.add('visible');
    } else {
      scrollBtn.classList.remove('visible');
    }
  });
  scrollBtn.addEventListener('click', () => {
    messagesEl.scrollTo({ top: messagesEl.scrollHeight, behavior: 'smooth' });
  });
}


/* ─── Message Rendering ────────────────────────────────────────────────────── */
function removeWelcome() {
  const wb = document.getElementById('welcome-block');
  if (wb) wb.remove();
}

function createMsgGroup(role) {
  const group = document.createElement('div');
  group.className = `msg-group ${role}`;

  const meta = document.createElement('div');
  meta.className = 'msg-meta';

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = role === 'user' ? '🧑' : '🤖';

  const time = document.createElement('span');
  const now  = new Date();
  time.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  meta.append(avatar, time);

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';

  group.append(meta, bubble);
  return { group, bubble };
}

function appendMessage(role, text) {
  removeWelcome();
  const { group, bubble } = createMsgGroup(role);
  // Render bold **text** as <strong>
  bubble.innerHTML = renderMarkdown(text);
  messagesEl.appendChild(group);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return bubble;
}

function renderMarkdown(text) {
  // Escape HTML first to prevent any script injections
  let safe = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  
  const links = [];
  
  // 1. Extract markdown links: [text](url)
  // Replace them with placeholders
  safe = safe.replace(/\[(.*?)\]\((https?:\/\/[^\s)]+)\)/g, function(match, label, url) {
    const placeholder = `__MD_LINK_PLACEHOLDER_${links.length}__`;
    links.push(`<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`);
    return placeholder;
  });
  
  // 2. Extract remaining plain URLs
  safe = safe.replace(/https?:\/\/[^\s<]+/g, function(url) {
    if (url.includes('__MD_LINK_PLACEHOLDER_')) {
      return url;
    }
    const placeholder = `__MD_LINK_PLACEHOLDER_${links.length}__`;
    links.push(`<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`);
    return placeholder;
  });
  
  // 3. Process other markdown formatting
  safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  safe = safe.replace(/\*(.*?)\*/g, '<em>$1</em>');
  safe = safe.replace(/\n/g, '<br>');
  
  // 4. Substitute placeholders back
  for (let i = 0; i < links.length; i++) {
    safe = safe.replace(`__MD_LINK_PLACEHOLDER_${i}__`, links[i]);
  }
  
  return safe;
}

function showLoading() {
  const { group, bubble } = createMsgGroup('bot');
  group.classList.add('loading');
  group.id = 'loading-group';
  bubble.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div>`;
  messagesEl.appendChild(group);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  if (stopBtn) stopBtn.disabled = false;
}

function removeLoading() {
  const lg = document.getElementById('loading-group');
  if (lg) lg.remove();
  if (stopBtn) stopBtn.disabled = true;
}

function stopCurrentRequest() {
  if (currentAbortController) {
    currentAbortController.abort();
    currentAbortController = null;
  }
  if (isBusy) {
    appendMessage('bot', '⏹️ Request stopped.');
  }
  isBusy = false;
  sendBtn.disabled = false;
  removeLoading();
}

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text || isBusy) return;

  inputEl.value = '';
  autoResize();

  appendMessage('user', text);
  isBusy = true;
  sendBtn.disabled = true;
  if (stopBtn) stopBtn.disabled = false;

  currentAbortController = new AbortController();
  const signal = currentAbortController.signal;

  showLoading();

  try {
    const res = await fetch('/api/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message: text }),
      signal,
    });
    removeLoading();

    if (!res.ok) {
      appendMessage('bot', '❌ Server error. Please try again.');
    } else {
      const data = await res.json();
      const reply = data.reply || 'I received an empty response. Please try again.';
      appendMessage('bot', reply);
    }
  } catch (err) {
    removeLoading();
    if (err.name === 'AbortError') {
      appendMessage('bot', '⏹️ Request stopped.');
    } else {
      appendMessage('bot', `❌ Connection error: ${err.message}. Make sure the server is running.`);
    }
  } finally {
    currentAbortController = null;
    isBusy = false;
    sendBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
    inputEl.focus();
  }
}

/* ─── Input handlers ───────────────────────────────────────────────────────── */
sendBtn.addEventListener('click', sendMessage);
if (stopBtn) stopBtn.addEventListener('click', stopCurrentRequest);

inputEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

function autoResize() {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 130) + 'px';
}
inputEl.addEventListener('input', autoResize);
