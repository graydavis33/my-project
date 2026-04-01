// ─── Init ─────────────────────────────────────────────────────
requireAuth();

let globalStats = null;
let currentView = 'overview';

// ─── View Switching ───────────────────────────────────────────
function switchView(view, linkEl) {
  currentView = view;

  // Update sidebar active state
  document.querySelectorAll('.sidebar-link[data-view]').forEach(el => el.classList.remove('active'));
  if (linkEl) linkEl.classList.add('active');

  // Hide all views
  document.querySelectorAll('[id^="view-"]').forEach(el => el.style.display = 'none');

  // Show target view
  const target = document.getElementById('view-' + view);
  if (target) target.style.display = 'block';

  // Populate platform view with current data if available
  if (globalStats && (view === 'youtube' || view === 'tiktok')) {
    renderPlatformView(view, globalStats);
  }
}

// ─── Fetch + Render Stats ─────────────────────────────────────
async function fetchStats() {
  showLoading(true);
  try {
    const data = await apiCall('/api/stats');
    globalStats = data;
    renderStats(data);
    fetchInsights();
  } catch (err) {
    showLoading(false);
    console.error('Failed to load stats:', err);
  }
}

function renderStats(data) {
  showLoading(false);

  const connections = data.connections || {};
  const hasAny = connections.youtube || connections.tiktok;

  renderPlatformBadges(connections);

  if (!hasAny) {
    document.getElementById('connect-prompt').style.display = 'block';
    document.getElementById('stats-section').style.display = 'none';
    return;
  }

  document.getElementById('connect-prompt').style.display = 'none';
  document.getElementById('stats-section').style.display = 'block';

  const allVideos = [
    ...(data.youtube?.videos || []),
    ...(data.tiktok?.videos || []),
  ];

  const totalViews = allVideos.reduce((s, v) => s + (v.views || 0), 0);
  const totalLikes = allVideos.reduce((s, v) => s + (v.likes || 0), 0);
  const totalComments = allVideos.reduce((s, v) => s + (v.comments || 0), 0);

  document.getElementById('stat-views').textContent = formatNumber(totalViews);
  document.getElementById('stat-likes').textContent = formatNumber(totalLikes);
  document.getElementById('stat-comments').textContent = formatNumber(totalComments);
  document.getElementById('stat-videos').textContent = formatNumber(allVideos.length);

  const lastUpdated = data.fetched_at ? 'Last updated ' + formatDate(data.fetched_at) : '';
  document.getElementById('last-updated').textContent = lastUpdated;

  renderTopPosts(allVideos, 'top-posts-body', true);

  // Refresh active platform view if not on overview
  if (currentView !== 'overview') {
    renderPlatformView(currentView, data);
  }
}

// ─── Platform-specific view ───────────────────────────────────
function renderPlatformView(platform, data) {
  if (platform === 'youtube') {
    const yt = data.youtube;
    if (!yt) return;

    const statsGrid = document.getElementById('yt-stats-grid');
    statsGrid.innerHTML = `
      <div class="stat-card"><div class="stat-label">Channel</div><div class="stat-value" style="font-size:1.2rem;">${escapeHtml(yt.channel_name || '—')}</div></div>
      <div class="stat-card"><div class="stat-label">Subscribers</div><div class="stat-value">${formatNumber(yt.subscriber_count)}</div></div>
      <div class="stat-card"><div class="stat-label">Total Videos</div><div class="stat-value">${formatNumber((yt.videos || []).length)}</div></div>
      <div class="stat-card"><div class="stat-label">Total Views</div><div class="stat-value">${formatNumber((yt.videos || []).reduce((s, v) => s + (v.views || 0), 0))}</div></div>
    `;
    renderTopPosts(yt.videos || [], 'yt-posts-body', false);
  }

  if (platform === 'tiktok') {
    const tt = data.tiktok;
    if (!tt) return;

    const statsGrid = document.getElementById('tt-stats-grid');
    statsGrid.innerHTML = `
      <div class="stat-card"><div class="stat-label">Account</div><div class="stat-value" style="font-size:1.2rem;">@${escapeHtml(tt.username || '—')}</div></div>
      <div class="stat-card"><div class="stat-label">Followers</div><div class="stat-value">${formatNumber(tt.follower_count)}</div></div>
      <div class="stat-card"><div class="stat-label">Total Videos</div><div class="stat-value">${formatNumber((tt.videos || []).length)}</div></div>
      <div class="stat-card"><div class="stat-label">Total Views</div><div class="stat-value">${formatNumber((tt.videos || []).reduce((s, v) => s + (v.views || 0), 0))}</div></div>
    `;
    renderTopPosts(tt.videos || [], 'tt-posts-body', false);
  }
}

// ─── Platform Badges ──────────────────────────────────────────
function renderPlatformBadges(connections) {
  const container = document.getElementById('platform-cards');
  const platforms = [
    { key: 'youtube', name: 'YouTube' },
    { key: 'tiktok', name: 'TikTok' },
  ];
  container.innerHTML = platforms.map(p => {
    const connected = !!connections[p.key];
    return `
      <div class="platform-badge ${connected ? 'connected' : 'disconnected'}">
        <div class="status-dot"></div>
        <div>
          <div class="platform-name">${p.name}</div>
          <div class="platform-status">${connected ? 'Connected' : 'Not connected'}</div>
        </div>
      </div>
    `;
  }).join('');
}

// ─── Posts Table ──────────────────────────────────────────────
function renderTopPosts(videos, tbodyId, showPlatform) {
  const tbody = document.getElementById(tbodyId);
  if (!videos.length) {
    const cols = showPlatform ? 7 : 6;
    tbody.innerHTML = `<tr><td colspan="${cols}" style="text-align:center;padding:2rem;color:var(--muted);">No data yet</td></tr>`;
    return;
  }

  const sorted = [...videos].sort((a, b) => (b.views || 0) - (a.views || 0)).slice(0, 50);
  const youtubeVideoId = (url) => {
    if (!url) return null;
    // youtu.be/ID or youtube.com/watch?v=ID
    const shortMatch = url.match(/youtu\.be\/([^?&]+)/);
    if (shortMatch) return shortMatch[1];
    try { return new URL(url).searchParams.get('v'); } catch { return null; }
  };

  tbody.innerHTML = sorted.map(v => {
    const vtId = youtubeVideoId(v.url);
    const isYT = v.platform === 'YouTube' && vtId;

    const watchBtn = isYT
      ? `<button class="btn btn-ghost btn-sm" onclick="openVideoModal('${escapeHtml(vtId)}', '${escapeHtml((v.title || '').replace(/'/g, "\\'"))}')">▶ Watch</button>`
      : v.url
        ? `<a href="${escapeHtml(v.url)}" target="_blank" rel="noopener" class="btn btn-ghost btn-sm">↗ Open</a>`
        : '';

    const commentBtn = isYT
      ? `<button class="btn btn-ghost btn-sm" style="margin-left:0.25rem;" onclick="openComments('${escapeHtml(vtId)}', '${escapeHtml((v.title || '').replace(/'/g, "\\'"))}')">💬</button>`
      : '';

    const platformCol = showPlatform ? `<td>${escapeHtml(v.platform || '—')}</td>` : '';

    return `
      <tr>
        <td>${escapeHtml(v.title || 'Untitled')}</td>
        ${platformCol}
        <td>${formatNumber(v.views)}</td>
        <td>${formatNumber(v.likes)}</td>
        <td>${formatNumber(v.comments)}</td>
        <td>${escapeHtml(v.published_at || v.published_date || '—')}</td>
        <td style="white-space:nowrap;">${watchBtn}${commentBtn}</td>
      </tr>
    `;
  }).join('');
}

// ─── Video Embed Modal ────────────────────────────────────────
function openVideoModal(videoId, title) {
  document.getElementById('video-modal-title').textContent = title;
  document.getElementById('video-modal-iframe').src =
    `https://www.youtube.com/embed/${videoId}?autoplay=1`;
  document.getElementById('video-modal-overlay').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeVideoModal(event) {
  if (event && event.target !== document.getElementById('video-modal-overlay')) return;
  document.getElementById('video-modal-iframe').src = '';
  document.getElementById('video-modal-overlay').classList.add('hidden');
  document.body.style.overflow = '';
}

// ─── Comments Panel ───────────────────────────────────────────
async function openComments(videoId, title) {
  const panel = document.getElementById('comments-panel');
  document.getElementById('comments-panel-title').textContent = `Comments — ${title}`;
  document.getElementById('comments-panel-body').innerHTML =
    '<div class="loading-state"><div class="spinner"></div><span>Fetching comments...</span></div>';
  panel.classList.add('open');

  try {
    const data = await apiCall(`/api/comments/youtube/${videoId}`);
    renderComments(data.comments || []);
  } catch (err) {
    document.getElementById('comments-panel-body').innerHTML =
      `<div class="empty-state"><p>Could not load comments.<br>${escapeHtml(err.message)}</p></div>`;
  }
}

function renderComments(comments) {
  const body = document.getElementById('comments-panel-body');
  if (!comments.length) {
    body.innerHTML = '<div class="empty-state"><p>No comments found for this video.</p></div>';
    return;
  }
  body.innerHTML = comments.map(c => `
    <div class="comment-item">
      <div class="comment-author">${escapeHtml(c.author)}</div>
      <div class="comment-text">${escapeHtml(c.text)}</div>
      <div class="comment-meta">👍 ${c.likes} · ${escapeHtml(c.published_at)}</div>
    </div>
  `).join('');
}

function closeComments() {
  document.getElementById('comments-panel').classList.remove('open');
}

// ─── Insights ─────────────────────────────────────────────────
async function fetchInsights(forceRegen = false) {
  const body = document.getElementById('insights-body');
  const dateEl = document.getElementById('insights-date');
  if (!body) return;

  body.textContent = 'Loading insights...';

  try {
    const path = forceRegen ? '/api/insights?force=true' : '/api/insights';
    const data = await apiCall(path);
    if (data.content) {
      body.textContent = data.content;
      if (data.generated_at) dateEl.textContent = 'Generated ' + formatDate(data.generated_at);
    } else {
      body.textContent = 'No insights yet — connect a platform and refresh your data.';
    }
  } catch (err) {
    body.textContent = 'Could not load insights.';
  }
}

// ─── Refresh ──────────────────────────────────────────────────
async function refreshStats() {
  const btn = document.getElementById('refresh-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Refreshing...';

  try {
    await apiCall('/api/stats/refresh', { method: 'POST' });
    await fetchStats();
  } catch (err) {
    console.error('Refresh failed:', err);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Refresh';
  }
}

// ─── Helpers ──────────────────────────────────────────────────
function showLoading(show) {
  document.getElementById('loading-state').style.display = show ? 'flex' : 'none';
  if (show) {
    document.getElementById('connect-prompt').style.display = 'none';
    document.getElementById('stats-section').style.display = 'none';
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Close video modal on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeVideoModal();
    closeComments();
  }
});

// ─── Boot ─────────────────────────────────────────────────────
fetchStats();
