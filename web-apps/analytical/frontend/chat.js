// ─── Init ─────────────────────────────────────────────────────
requireAuth();

let history = [];
let isLoading = false;

// ─── Send message ─────────────────────────────────────────────
async function sendMessage() {
  const input = document.getElementById('chat-input');
  const message = input.value.trim();
  if (!message || isLoading) return;

  input.value = '';
  autoResize(input);

  // Switch from empty state to message thread
  document.getElementById('chat-empty').style.display = 'none';
  document.getElementById('chat-messages').style.display = 'flex';

  // Append user message
  appendMessage('user', message);

  // Show typing indicator
  const typingId = appendTyping();

  isLoading = true;
  document.getElementById('chat-send-btn').disabled = true;

  try {
    const data = await apiCall('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message, history }),
    });

    removeTyping(typingId);
    const response = data.response || 'No response received.';
    appendMessage('assistant', response);

    // Update history
    history.push({ role: 'user', content: message });
    history.push({ role: 'assistant', content: response });

    // Keep history bounded
    if (history.length > 24) history = history.slice(-24);

  } catch (err) {
    removeTyping(typingId);
    appendMessage('assistant', `Error: ${err.message}. Make sure the backend is running.`);
  } finally {
    isLoading = false;
    document.getElementById('chat-send-btn').disabled = false;
    input.focus();
  }
}

function sendSuggestion(btn) {
  document.getElementById('chat-input').value = btn.textContent;
  sendMessage();
}

// ─── Message rendering ────────────────────────────────────────
function appendMessage(role, text) {
  const thread = document.getElementById('chat-messages');

  const avatarContent = role === 'user' ? '👤' : '🤖';

  const div = document.createElement('div');
  div.className = `chat-message ${role}`;
  div.innerHTML = `
    <div class="chat-avatar">${avatarContent}</div>
    <div class="chat-bubble">${renderMarkdown(text)}</div>
  `;
  thread.appendChild(div);
  thread.scrollTop = thread.scrollHeight;
  return div;
}

function appendTyping() {
  const thread = document.getElementById('chat-messages');
  const id = 'typing-' + Date.now();
  const div = document.createElement('div');
  div.className = 'chat-message assistant';
  div.id = id;
  div.innerHTML = `
    <div class="chat-avatar">🤖</div>
    <div class="chat-bubble"><div class="chat-typing"><span></span><span></span><span></span></div></div>
  `;
  thread.appendChild(div);
  thread.scrollTop = thread.scrollHeight;
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ─── Lightweight Markdown renderer ───────────────────────────
function renderMarkdown(text) {
  let html = escapeHtmlChat(text);

  // Bold **text**
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Bullet lists (lines starting with - or *)
  html = html.replace(/^[\-\*] (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

  // Numbered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

  // Headings ## and ###
  html = html.replace(/^### (.+)$/gm, '<strong>$1</strong>');
  html = html.replace(/^## (.+)$/gm, '<strong style="font-size:1.05em;">$1</strong>');

  // Line breaks → paragraphs
  const lines = html.split('\n');
  const paras = [];
  let current = '';
  for (const line of lines) {
    if (line.trim() === '') {
      if (current.trim()) paras.push(`<p>${current.trim()}</p>`);
      current = '';
    } else {
      current += (current ? ' ' : '') + line;
    }
  }
  if (current.trim()) paras.push(`<p>${current.trim()}</p>`);

  return paras.join('') || html;
}

function escapeHtmlChat(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// ─── Input helpers ────────────────────────────────────────────
function handleChatKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 140) + 'px';
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
