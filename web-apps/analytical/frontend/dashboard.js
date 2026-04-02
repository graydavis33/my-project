// ─── Init ─────────────────────────────────────────────────────
requireAuth();

let globalStats = null;
let currentView = 'overview';
let chartInstances = {};

// Chart defaults — gold on dark navy
Chart.defaults.color = '#8899aa';
Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
Chart.defaults.font.family = "'Inter', sans-serif";

// ─── View Switching ───────────────────────────────────────────
function switchView(view, linkEl) {
  currentView = view;

  document.querySelectorAll('.sidebar-link[data-view]').forEach(el => el.classList.remove('active'));
  if (linkEl) linkEl.classList.add('active');

  document.querySelectorAll('[id^="view-"]').forEach(el => el.style.display = 'none');
  const target = document.getElementById('view-' + view);
  if (target) target.style.display = 'block';

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

  const totalViews    = allVideos.reduce((s, v) => s + (v.views || 0), 0);
  const totalLikes    = allVideos.reduce((s, v) => s + (v.likes || 0), 0);
  const totalComments = allVideos.reduce((s, v) => s + (v.comments || 0), 0);
  const totalShares   = allVideos.reduce((s, v) => s + (v.shares || 0), 0);
  const totalFollowers = (data.youtube?.subscriber_count || 0) + (data.tiktok?.follower_count || 0);
  const engRate = totalViews > 0
    ? ((totalLikes + totalComments + totalShares) / totalViews * 100).toFixed(1) + '%'
    : '—';

  document.getElementById('stat-followers').textContent  = formatNumber(totalFollowers);
  document.getElementById('stat-views').textContent      = formatNumber(totalViews);
  document.getElementById('stat-likes').textContent      = formatNumber(totalLikes);
  document.getElementById('stat-comments').textContent   = formatNumber(totalComments);
  document.getElementById('stat-shares').textContent     = formatNumber(totalShares);
  document.getElementById('stat-videos').textContent     = formatNumber(allVideos.length);
  document.getElementById('stat-engagement').textContent = engRate;

  const lastUpdated = data.fetched_at ? 'Last updated ' + formatDate(data.fetched_at) : '';
  document.getElementById('last-updated').textContent = lastUpdated;

  renderTopPosts(allVideos, 'top-posts-body', true);
  renderOverviewChart(data);

  if (currentView !== 'overview') {
    renderPlatformView(currentView, data);
  }
}

// ─── Platform-specific view ───────────────────────────────────
function renderPlatformView(platform, data) {
  if (platform === 'youtube') {
    const yt = data.youtube;
    if (!yt) return;

    const videos = yt.videos || [];
    const totalViews = videos.reduce((s, v) => s + (v.views || 0), 0);
    const totalLikes = videos.reduce((s, v) => s + (v.likes || 0), 0);
    const engRate = totalViews > 0
      ? ((totalLikes + videos.reduce((s,v)=>s+(v.comments||0),0)) / totalViews * 100).toFixed(1) + '%'
      : '—';

    document.getElementById('yt-stats-grid').innerHTML = `
      <div class="stat-card"><div class="stat-label">Channel</div><div class="stat-value" style="font-size:1.2rem;">${escapeHtml(yt.channel_name || '—')}</div></div>
      <div class="stat-card"><div class="stat-label">Subscribers</div><div class="stat-value">${formatNumber(yt.subscriber_count)}</div></div>
      <div class="stat-card"><div class="stat-label">Total Videos</div><div class="stat-value">${formatNumber(videos.length)}</div></div>
      <div class="stat-card"><div class="stat-label">Total Views</div><div class="stat-value">${formatNumber(totalViews)}</div></div>
      <div class="stat-card"><div class="stat-label">Total Likes</div><div class="stat-value">${formatNumber(totalLikes)}</div></div>
      <div class="stat-card"><div class="stat-label">Engagement Rate</div><div class="stat-value">${engRate}</div></div>
    `;

    // Advanced metrics (YouTube-specific analytics fields)
    const hasAdvanced = videos.some(v => v.watch_time_minutes || v.impressions || v.ctr_pct);
    if (hasAdvanced) {
      const totalWatchTime = videos.reduce((s, v) => s + (v.watch_time_minutes || 0), 0);
      const totalImpressions = videos.reduce((s, v) => s + (v.impressions || 0), 0);
      const avgCTR = videos.filter(v => v.ctr_pct).length
        ? (videos.reduce((s, v) => s + (v.ctr_pct || 0), 0) / videos.filter(v => v.ctr_pct).length).toFixed(1) + '%'
        : '—';
      const avgViewPct = videos.filter(v => v.avg_view_pct).length
        ? (videos.reduce((s, v) => s + (v.avg_view_pct || 0), 0) / videos.filter(v => v.avg_view_pct).length).toFixed(1) + '%'
        : '—';
      const subsGained = videos.reduce((s, v) => s + (v.subscribers_gained || 0), 0);

      document.getElementById('yt-advanced-metrics').innerHTML = `
        <div class="stat-card"><div class="stat-label">Watch Time (min)</div><div class="stat-value">${formatNumber(Math.round(totalWatchTime))}</div></div>
        <div class="stat-card"><div class="stat-label">Total Impressions</div><div class="stat-value">${formatNumber(totalImpressions)}</div></div>
        <div class="stat-card"><div class="stat-label">Avg CTR</div><div class="stat-value">${avgCTR}</div></div>
        <div class="stat-card"><div class="stat-label">Avg View %</div><div class="stat-value">${avgViewPct}</div></div>
        <div class="stat-card"><div class="stat-label">Subs Gained</div><div class="stat-value">${formatNumber(subsGained)}</div></div>
      `;
      document.getElementById('yt-advanced-toggle').style.display = 'flex';
    } else {
      document.getElementById('yt-advanced-toggle').style.display = 'none';
    }

    renderTopPosts(videos, 'yt-posts-body', false, 'youtube');
    renderBarChart('chart-yt-bar', videos);
    renderLineChart('chart-yt-line', videos);
  }

  if (platform === 'tiktok') {
    const tt = data.tiktok;
    if (!tt) return;

    const videos = tt.videos || [];
    const totalViews = videos.reduce((s, v) => s + (v.views || 0), 0);
    const totalLikes = videos.reduce((s, v) => s + (v.likes || 0), 0);
    const totalShares = videos.reduce((s, v) => s + (v.shares || 0), 0);
    const engRate = totalViews > 0
      ? ((totalLikes + videos.reduce((s,v)=>s+(v.comments||0),0) + totalShares) / totalViews * 100).toFixed(1) + '%'
      : '—';

    document.getElementById('tt-stats-grid').innerHTML = `
      <div class="stat-card"><div class="stat-label">Account</div><div class="stat-value" style="font-size:1.2rem;">@${escapeHtml(tt.username || '—')}</div></div>
      <div class="stat-card"><div class="stat-label">Followers</div><div class="stat-value">${formatNumber(tt.follower_count)}</div></div>
      <div class="stat-card"><div class="stat-label">Total Videos</div><div class="stat-value">${formatNumber(videos.length)}</div></div>
      <div class="stat-card"><div class="stat-label">Total Views</div><div class="stat-value">${formatNumber(totalViews)}</div></div>
      <div class="stat-card"><div class="stat-label">Total Likes</div><div class="stat-value">${formatNumber(totalLikes)}</div></div>
      <div class="stat-card"><div class="stat-label">Engagement Rate</div><div class="stat-value">${engRate}</div></div>
    `;

    renderTopPosts(videos, 'tt-posts-body', false, 'tiktok');
    renderBarChart('chart-tt-bar', videos);
    renderLineChart('chart-tt-line', videos);
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
function engagementRate(v) {
  const views = v.views || 0;
  if (!views) return 0;
  return ((v.likes || 0) + (v.comments || 0) + (v.shares || 0)) / views * 100;
}

function renderTopPosts(videos, tbodyId, showPlatform, platform) {
  const tbody = document.getElementById(tbodyId);
  if (!videos.length) {
    const cols = showPlatform ? 8 : (platform === 'tiktok' ? 8 : 7);
    tbody.innerHTML = `<tr><td colspan="${cols}" style="text-align:center;padding:2rem;color:var(--muted);">No data yet</td></tr>`;
    return;
  }

  const sorted = [...videos].sort((a, b) => (b.views || 0) - (a.views || 0)).slice(0, 50);

  const youtubeVideoId = (url) => {
    if (!url) return null;
    const shortMatch = url.match(/youtu\.be\/([^?&]+)/);
    if (shortMatch) return shortMatch[1];
    try { return new URL(url).searchParams.get('v'); } catch { return null; }
  };

  tbody.innerHTML = sorted.map(v => {
    const vtId = youtubeVideoId(v.url);
    const isYT = (v.platform === 'YouTube' || platform === 'youtube') && vtId;
    const isTT = v.platform === 'TikTok' || platform === 'tiktok';

    // Thumbnail
    let thumbHtml;
    if (isYT) {
      thumbHtml = `<img class="video-thumb" src="https://img.youtube.com/vi/${escapeHtml(vtId)}/mqdefault.jpg" alt="" loading="lazy">`;
    } else {
      thumbHtml = `<div class="thumb-placeholder">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.32 6.32 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V9.01a8.16 8.16 0 004.77 1.52V7.07a4.85 4.85 0 01-1-.38z"/></svg>
      </div>`;
    }

    const watchBtn = isYT
      ? `<button class="btn btn-ghost btn-sm" onclick="openVideoModal('${escapeHtml(vtId)}', '${escapeHtml((v.title || '').replace(/'/g, "\\'"))}')">▶ Watch</button>`
      : v.url
        ? `<a href="${escapeHtml(v.url)}" target="_blank" rel="noopener" class="btn btn-ghost btn-sm">↗ Open</a>`
        : '';

    const commentBtn = isYT
      ? `<button class="btn btn-ghost btn-sm" style="margin-left:0.25rem;" onclick="openComments('${escapeHtml(vtId)}', '${escapeHtml((v.title || '').replace(/'/g, "\\'"))}')">💬</button>`
      : '';

    const platformCol = showPlatform ? `<td>${escapeHtml(v.platform || '—')}</td>` : '';
    const sharesCol = (isTT && !showPlatform) ? `<td>${formatNumber(v.shares)}</td>` : '';
    const eng = engagementRate(v).toFixed(1) + '%';

    return `
      <tr>
        <td style="padding:0.5rem 1rem;">${thumbHtml}</td>
        <td>
          <div class="thumb-cell">
            <span class="video-title">${escapeHtml(v.title || 'Untitled')}</span>
          </div>
        </td>
        ${platformCol}
        <td>${formatNumber(v.views)}</td>
        <td>${formatNumber(v.likes)}</td>
        ${sharesCol}
        <td>${eng}</td>
        <td>${escapeHtml(v.published_at || v.published_date || '—')}</td>
        <td style="white-space:nowrap;">${watchBtn}${commentBtn}</td>
      </tr>
    `;
  }).join('');
}

// ─── Filters ──────────────────────────────────────────────────
function applyFilters() {
  if (!globalStats) return;
  const platform = document.getElementById('filter-platform').value;
  const sortBy   = document.getElementById('filter-sort').value;

  let videos = [
    ...(globalStats.youtube?.videos || []),
    ...(globalStats.tiktok?.videos || []),
  ];

  if (platform !== 'all') videos = videos.filter(v => v.platform === platform);

  videos.sort((a, b) => {
    if (sortBy === 'likes')      return (b.likes || 0) - (a.likes || 0);
    if (sortBy === 'comments')   return (b.comments || 0) - (a.comments || 0);
    if (sortBy === 'engagement') return engagementRate(b) - engagementRate(a);
    return (b.views || 0) - (a.views || 0);
  });

  renderTopPosts(videos, 'top-posts-body', true);
}

function applyYTFilters() {
  if (!globalStats?.youtube) return;
  const type   = document.getElementById('filter-yt-type').value;
  const sortBy = document.getElementById('filter-yt-sort').value;

  let videos = [...(globalStats.youtube.videos || [])];

  if (type === 'short')  videos = videos.filter(v => v.is_short);
  if (type === 'long')   videos = videos.filter(v => !v.is_short);

  videos.sort((a, b) => {
    if (sortBy === 'likes')      return (b.likes || 0) - (a.likes || 0);
    if (sortBy === 'comments')   return (b.comments || 0) - (a.comments || 0);
    if (sortBy === 'engagement') return engagementRate(b) - engagementRate(a);
    return (b.views || 0) - (a.views || 0);
  });

  renderTopPosts(videos, 'yt-posts-body', false, 'youtube');
}

function applyTTFilters() {
  if (!globalStats?.tiktok) return;
  const sortBy = document.getElementById('filter-tt-sort').value;

  let videos = [...(globalStats.tiktok.videos || [])];

  videos.sort((a, b) => {
    if (sortBy === 'likes')      return (b.likes || 0) - (a.likes || 0);
    if (sortBy === 'comments')   return (b.comments || 0) - (a.comments || 0);
    if (sortBy === 'shares')     return (b.shares || 0) - (a.shares || 0);
    if (sortBy === 'engagement') return engagementRate(b) - engagementRate(a);
    return (b.views || 0) - (a.views || 0);
  });

  renderTopPosts(videos, 'tt-posts-body', false, 'tiktok');
}

// ─── Advanced Metrics Toggle ──────────────────────────────────
function toggleAdvanced(platform) {
  const btn = document.getElementById(`${platform}-advanced-toggle`);
  const panel = document.getElementById(`${platform}-advanced-metrics`);
  const isOpen = btn.classList.toggle('open');
  panel.classList.toggle('open', isOpen);
}

// ─── Charts ───────────────────────────────────────────────────
const GOLD = '#e8b84b';
const GOLD_DIM = 'rgba(232,184,75,0.15)';
const GOLD_LINE = 'rgba(232,184,75,0.8)';

function chartConfig(labels, data, type) {
  if (type === 'bar') {
    return {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: GOLD_DIM,
          borderColor: GOLD,
          borderWidth: 1.5,
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ' ' + formatNumber(ctx.raw) } } },
        scales: {
          x: { ticks: { maxRotation: 30, font: { size: 10 } }, grid: { display: false } },
          y: { ticks: { callback: v => formatNumber(v), font: { size: 10 } } }
        }
      }
    };
  }

  // line
  return {
    type: 'line',
    data: {
      labels,
      datasets: [{
        data,
        borderColor: GOLD_LINE,
        backgroundColor: GOLD_DIM,
        fill: true,
        tension: 0.35,
        pointRadius: 3,
        pointBackgroundColor: GOLD,
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ' ' + formatNumber(ctx.raw) } } },
      scales: {
        x: { ticks: { maxRotation: 30, font: { size: 10 } }, grid: { display: false } },
        y: { ticks: { callback: v => formatNumber(v), font: { size: 10 } } }
      }
    }
  };
}

function renderBarChart(canvasId, videos) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  if (chartInstances[canvasId]) chartInstances[canvasId].destroy();

  const top10 = [...videos].sort((a, b) => (b.views || 0) - (a.views || 0)).slice(0, 10);
  const labels = top10.map(v => (v.title || 'Untitled').slice(0, 20) + (v.title?.length > 20 ? '…' : ''));
  const data   = top10.map(v => v.views || 0);

  chartInstances[canvasId] = new Chart(canvas, chartConfig(labels, data, 'bar'));
}

function renderLineChart(canvasId, videos) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  if (chartInstances[canvasId]) chartInstances[canvasId].destroy();

  const sorted = [...videos]
    .filter(v => v.published_at)
    .sort((a, b) => a.published_at.localeCompare(b.published_at));

  const labels = sorted.map(v => v.published_at);
  const data   = sorted.map(v => v.views || 0);

  chartInstances[canvasId] = new Chart(canvas, chartConfig(labels, data, 'line'));
}

function renderOverviewChart(data) {
  const canvas = document.getElementById('chart-overview');
  if (!canvas) return;

  if (chartInstances['chart-overview']) chartInstances['chart-overview'].destroy();

  const platforms = [];
  const totals = [];

  if (data.youtube?.videos?.length) {
    platforms.push('YouTube');
    totals.push(data.youtube.videos.reduce((s, v) => s + (v.views || 0), 0));
  }
  if (data.tiktok?.videos?.length) {
    platforms.push('TikTok');
    totals.push(data.tiktok.videos.reduce((s, v) => s + (v.views || 0), 0));
  }

  chartInstances['chart-overview'] = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: platforms,
      datasets: [{
        data: totals,
        backgroundColor: [GOLD_DIM, 'rgba(255,255,255,0.08)'],
        borderColor: [GOLD, 'rgba(255,255,255,0.3)'],
        borderWidth: 1.5,
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => ' ' + formatNumber(ctx.raw) + ' views' } } },
      scales: {
        x: { grid: { display: false } },
        y: { ticks: { callback: v => formatNumber(v) } }
      }
    }
  });
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
      `<div class="empty-state"><p>Could not load comments.<br><small style="color:var(--muted)">${escapeHtml(err.message)}</small></p></div>`;
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

  body.textContent = 'Analyzing your data...';

  try {
    const path = forceRegen ? '/api/insights?force=true' : '/api/insights';
    const data = await apiCall(path);
    if (data.content) {
      body.innerHTML = renderInsightsMarkdown(data.content);
      if (data.generated_at) dateEl.textContent = 'Generated ' + formatDate(data.generated_at);
    } else {
      body.textContent = 'No insights yet — connect a platform and refresh your data.';
    }
  } catch (err) {
    body.textContent = 'Could not load insights.';
  }
}

function renderInsightsMarkdown(text) {
  // Bold section titles (**Title**)
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong style="color:var(--text);">$1</strong>')
    .replace(/\n/g, '<br>');
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

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeVideoModal();
    closeComments();
  }
});

// ─── Boot ─────────────────────────────────────────────────────
requireAuth().then(() => fetchStats());
