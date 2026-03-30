// ─── Config ──────────────────────────────────────────────────
// Change this to your Railway URL when deployed
const API_BASE = 'http://localhost:8000';

function getApiBase() {
  return API_BASE;
}

// ─── Auth Helpers ─────────────────────────────────────────────
function getToken() {
  return localStorage.getItem('token');
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = 'login.html';
  }
}

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.location.href = 'login.html';
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
    // Token expired or invalid — force logout
    logout();
    throw new Error('Session expired. Please log in again.');
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
