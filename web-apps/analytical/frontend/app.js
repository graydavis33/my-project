// ─── Config ──────────────────────────────────────────────────
// Change this to your Railway URL when deployed
const API_BASE = 'http://localhost:8000';

function getApiBase() {
  return API_BASE;
}

// ─── Auth Helpers ─────────────────────────────────────────────
const LOCAL_EMAIL = 'local@analytical.app';
const LOCAL_PASS  = 'localdev123';

function getToken() {
  return localStorage.getItem('token');
}

async function requireAuth() {
  if (getToken()) return;

  // Auto-login as the local user (create account if first run)
  try {
    const res = await fetch(API_BASE + '/api/auth/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: LOCAL_EMAIL, password: LOCAL_PASS }),
    });
    const data = await res.json();
    if (data.token) {
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      return;
    }
  } catch {}

  // Account already exists — login instead
  try {
    const res = await fetch(API_BASE + '/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: LOCAL_EMAIL, password: LOCAL_PASS }),
    });
    const data = await res.json();
    if (data.token) {
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
    }
  } catch {}
}

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.location.href = 'dashboard.html';
}

// ─── API Call Wrapper ─────────────────────────────────────────
async function apiCall(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const res = await fetch(API_BASE + path, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    // Token expired — clear and re-auth next page load
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    await requireAuth();
    throw new Error('Session refreshed — please try again.');
  }

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || data.message || `Request failed (${res.status})`);
  }

  return data;
}

// ─── Formatting Helpers ───────────────────────────────────────
function formatNumber(n) {
  if (n == null) return '—';
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return n.toLocaleString();
}

function formatDate(isoStr) {
  if (!isoStr) return '—';
  return new Date(isoStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// ─── User State ───────────────────────────────────────────────
// Populate user email in nav if present
document.addEventListener('DOMContentLoaded', () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const emailEl = document.getElementById('user-email');
  if (emailEl && user.email) emailEl.textContent = user.email;

  // Set upgrade link based on tier
  const upgradeLink = document.getElementById('upgrade-link');
  if (upgradeLink) {
    if (user.tier === 'creator' || user.tier === 'pro') {
      upgradeLink.textContent = '⭐ Manage billing';
      upgradeLink.onclick = async (e) => {
        e.preventDefault();
        try {
          const data = await apiCall('/api/billing/portal');
          window.location.href = data.portal_url;
        } catch (err) {
          alert('Could not open billing portal: ' + err.message);
        }
      };
    } else {
      upgradeLink.onclick = async (e) => {
        e.preventDefault();
        try {
          const data = await apiCall('/api/billing/subscribe', { method: 'POST' });
          window.location.href = data.checkout_url;
        } catch (err) {
          alert('Could not start checkout: ' + err.message);
        }
      };
    }
  }
});
