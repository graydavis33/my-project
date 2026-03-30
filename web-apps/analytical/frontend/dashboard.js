// ─── Dashboard Entry Point ────────────────────────────────────
requireAuth();

let statsData = null;

// ─── Fetch + Render Stats ─────────────────────────────────────
async function fetchStats() {
  showLoading(true);
  try {
    const data = await apiCall('/api/stats');
    statsData = data;
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

  // Platform badges
  renderPlatformBadges(connections);

  if (!hasAny) {
    document.getElementById('connect-prompt').style.display = 'block';
    document.getElementById('stats-section').style.display = 'none';
    return;
  }

  document.getElementById('connect-prompt').style.display = 'none';
  document.getElementById('stats-section').style.display = 'block';

  // Aggregate stats across all platforms
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

  // Last updated
  const lastUpdated = data.fetched_at
    ? 'Last updated ' + formatDate(data.fetched_at)
    : '';
  document.getElementById('last-updated').textContent = lastUpdated;

  // Top posts table
  renderTopPosts(allVideos);
}

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

function renderTopPosts(videos) {
  const tbody = document.getElementById('top-posts-body');
  if (!videos.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:2rem; color:var(--muted);">No data yet</td></tr>';
    return;
  }

  const sorted = [...videos].sort((a, b) => (b.views || 0) - (a.views || 0)).slice(0, 20);

  tbody.innerHTML = sorted.map(v => `
    <tr>
      <td>
        ${v.url
          ? `<a href="${v.url}" target="_blank" rel="noopener" style="color:var(--text);">${escapeHtml(v.title || 'Untitled')}</a>`
          : escapeHtml(v.title || 'Untitled')
        }
      </td>
      <td>${escapeHtml(v.platform || '—')}</td>
      <td>${formatNumber(v.views)}</td>
      <td>${formatNumber(v.likes)}</td>
      <td>${formatNumber(v.comments)}</td>
      <td>${escapeHtml(v.published_at || v.published_date || '—')}</td>
    </tr>
  `).join('');
}

// ─── Fetch + Render Insights ──────────────────────────────────
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
      if (data.generated_at) {
        dateEl.textContent = 'Generated ' + formatDate(data.generated_at);
      }
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

// ─── Init ─────────────────────────────────────────────────────
fetchStats();
