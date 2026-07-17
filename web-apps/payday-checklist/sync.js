'use strict';
// sync.js — Payday Checklist cross-device sync engine.
// Local IndexedDB stays the UI's store; this mirrors mutations to a backend
// (Firestore in production, window.__SYNC_BACKEND fake in tests) and applies
// remote snapshots with last-write-wins by updated_at + tombstone deletes.
// If window.FIREBASE_CONFIG is null, Sync.init() hides the UI row and every
// hook is a no-op — the app behaves exactly like Phase 1.

const Sync = (() => {
  const ROOT = 'households/gray';
  const ALLOWED_EMAIL = 'graydavis33@gmail.com';
  const SETTING_KEYS = ['income', 'allocations', 'budgets', 'fund', 'ring', 'steps', 'notes', 'overrides', 'dismissed_gmail', 'business_vendors', 'reimburse_vendors'];

  let backend = null;
  let active = false;         // signed in + subscribed
  let applyingRemote = false; // guard: remote application must not re-mirror

  // Write mutex — serializes the two bulk writers (applyRemote + the app's
  // loadGmailExpenses) so a snapshot arriving mid-merge can't double-insert
  // the same transaction.
  let _lock = Promise.resolve();
  function withLock(fn) {
    const run = _lock.then(fn, fn);
    _lock = run.catch(() => {});
    return run;
  }

  // ── status UI ──
  function setStatus(text) {
    const el = document.getElementById('cloud-sync-status');
    if (el) el.textContent = text;
    const btn = document.getElementById('cloud-sync-btn');
    if (btn) btn.textContent = active ? 'sign out' : 'sign in';
  }

  // ── FirebaseBackend ──
  function makeFirebaseBackend(config) {
    firebase.initializeApp(config);
    const auth = firebase.auth();
    const fs = firebase.firestore();
    fs.enablePersistence({ synchronizeTabs: true }).catch(() => {});
    return {
      set: (path, data) => fs.doc(ROOT + '/' + path).set(data),
      subscribe(cb) {
        const unsubs = ['transactions', 'settings', 'history'].map(col =>
          fs.collection(ROOT + '/' + col).onSnapshot(snap => {
            const docs = {};
            snap.forEach(d => { docs[col + '/' + d.id] = d.data(); });
            cb(docs);
          })
        );
        return () => unsubs.forEach(u => u());
      },
      async signIn() {
        const provider = new firebase.auth.GoogleAuthProvider();
        try { await auth.signInWithPopup(provider); }
        catch (e) { await auth.signInWithRedirect(provider); }
      },
      signOut: () => auth.signOut(),
      onAuth(cb) {
        auth.onAuthStateChanged(u => {
          if (u && u.email !== ALLOWED_EMAIL) { auth.signOut(); cb(null); return; }
          cb(u);
        });
      }
    };
  }

  // ── local application of remote docs ──
  function applyRemote(docs) {
    return withLock(() => applyRemoteLocked(docs));
  }

  async function applyRemoteLocked(docs) {
    applyingRemote = true;
    try {
      let txnChanged = false, settingsChanged = false;
      const allLocal = await getAllTransactions();
      const allBySid = {};
      allLocal.forEach(t => { if (t.sid) allBySid[t.sid] = t; });

      for (const [path, data] of Object.entries(docs)) {
        const col = path.slice(0, path.indexOf('/'));
        const id = path.slice(path.indexOf('/') + 1);
        if (col === 'transactions') {
          const local = allBySid[id];
          if (local && (local.updatedAt || 0) >= (data.updated_at || 0)) continue;
          const rec = {
            ...(local || {}),
            sid: id, vendor: data.vendor, amount: data.amount, category: data.category,
            date: data.date, month: data.month, note: data.note || '',
            source: data.source || 'manual', deleted: !!data.deleted,
            createdAt: local ? local.createdAt : new Date(data.createdAt || Date.now()).toISOString(),
            updatedAt: data.updated_at || 0
          };
          if (data.email_id) rec.email_id = data.email_id;
          if (data.kind) rec.kind = data.kind;
          if (data.business != null) rec.business = data.business;
          if (data.reimburse) rec.reimburse = data.reimburse; else delete rec.reimburse;
          const newId = await addTransaction(rec);
          if (rec.id == null) rec.id = newId;
          allBySid[id] = rec;
          txnChanged = true;
        } else if (col === 'settings') {
          if (!SETTING_KEYS.includes(id)) continue;
          const meta = await getSetting('_syncmeta_' + id, 0);
          if (meta >= (data.updated_at || 0)) continue;
          await setSetting(id, data.value);            // applyingRemote guard stops re-mirroring
          await setSetting('_syncmeta_' + id, data.updated_at || 0);
          settingsChanged = true;
        } else if (col === 'history') {
          if (data.deleted) { await deleteHistory(Number(id)); }
          else if (data.entry) { await putHistory(data.entry); }
        }
      }

      if (txnChanged) {
        TXN_CACHE = (await getAllTransactions()).filter(t => !t.deleted);
        refreshExpenseDisplays();
      }
      if (settingsChanged) await reloadSettingsIntoUI();
      if (txnChanged || settingsChanged) setStatus('✓ synced');
    } finally {
      applyingRemote = false;
    }
  }

  // Re-read synced settings into the live UI (mirror of init()'s load block)
  async function reloadSettingsIntoUI() {
    const income = await getSetting('income', { biweekly: 3250, taxPct: 30 });
    const allocs = await getSetting('allocations', { rent: 1900, loans: 1000, ef: 400, ring: 200 });
    const budgets = await getSetting('budgets', null);
    const fund = await getSetting('fund', { balance: '', goal: 12000 });
    const ring = await getSetting('ring', { balance: '', goal: 10000 });
    const steps = await getSetting('steps', {});
    document.getElementById('paycheck-amount').value = income.biweekly;
    document.getElementById('tax-percent').value = income.taxPct;
    document.getElementById('alloc-tax').value = allocs.tax != null
      ? allocs.tax : Math.round(income.biweekly * 2 * income.taxPct / 100);
    document.getElementById('alloc-rent').value = allocs.rent;
    document.getElementById('alloc-loans').value = allocs.loans;
    document.getElementById('alloc-ef').value = allocs.ef;
    document.getElementById('alloc-ring').value = allocs.ring;
    document.getElementById('fund-balance').value = fund.balance;
    document.getElementById('fund-goal').value = fund.goal;
    document.getElementById('ring-balance').value = ring.balance;
    document.getElementById('ring-goal').value = ring.goal;
    document.getElementById('notes').value = await getSetting('notes', '');
    if (budgets && budgets.length === CATEGORIES.length) {
      BUDGETS = [...budgets];
      BUDGETS.forEach((b, i) => document.getElementById('budget-' + i).value = b);
    }
    OVERRIDES = await getSetting('overrides', {});
    BUSINESS_VENDORS = await getSetting('business_vendors', []);
    REIMBURSE_VENDORS = await getSetting('reimburse_vendors', []);
    if (typeof renderBusiness === 'function') renderBusiness();
    for (let i = 0; i < STEP_NAMES.length; i++)
      document.getElementById('step-' + i).classList.toggle('done', !!steps[i]);
    await updateAllocations(false);
    await updateFund(false);
    await updateRing(false);
    refreshExpenseDisplays();
  }

  // ── mirroring local → cloud ──
  function txnDoc(t) {
    return {
      vendor: t.vendor, amount: t.amount, category: t.category, date: t.date,
      month: t.month, note: t.note || '', source: t.source || 'manual',
      ...(t.email_id ? { email_id: t.email_id } : {}),
      ...(t.kind ? { kind: t.kind } : {}),
      ...(t.business != null ? { business: t.business } : {}),
      ...(t.reimburse ? { reimburse: t.reimburse } : {}),
      deleted: !!t.deleted,
      createdAt: Date.parse(t.createdAt || '') || Date.now(),
      updated_at: t.updatedAt || Date.now()
    };
  }

  function onLocalTxn(t) {
    if (!active || applyingRemote || !t.sid) return;
    backend.set('transactions/' + t.sid, txnDoc(t)).catch(() => setStatus('⚠ sync error'));
  }
  function onLocalTxnDelete(t) { onLocalTxn(t); }   // tombstone rides the same doc
  async function onLocalSetting(key, value) {
    if (!active || applyingRemote || !SETTING_KEYS.includes(key)) return;
    const now = Date.now();
    await setSetting('_syncmeta_' + key, now);
    backend.set('settings/' + key, { value: value, updated_at: now }).catch(() => setStatus('⚠ sync error'));
  }
  function onLocalHistory(entry) {
    if (!active || applyingRemote) return;
    backend.set('history/' + entry.id, { entry: entry, deleted: false, updated_at: Date.now() }).catch(() => {});
  }
  function onLocalHistoryDelete(id) {
    if (!active || applyingRemote) return;
    backend.set('history/' + id, { entry: null, deleted: true, updated_at: Date.now() }).catch(() => {});
  }

  // ── first-sign-in migration: push everything local up ──
  async function migrateUp() {
    const done = await getSetting('sync_migrated', false);
    if (done) return;
    const txns = await getAllTransactions();
    for (const t of txns) {
      if (!t.sid) {
        t.sid = t.email_id || uuidSid();
        t.updatedAt = Date.now();
        await addTransaction(t);
      }
      await backend.set('transactions/' + t.sid, txnDoc(t));
    }
    TXN_CACHE = (await getAllTransactions()).filter(t => !t.deleted);
    for (const key of SETTING_KEYS) {
      const v = await getSetting(key);
      if (v != null) {
        const now = Date.now();
        await setSetting('_syncmeta_' + key, now);
        await backend.set('settings/' + key, { value: v, updated_at: now });
      }
    }
    for (const h of await getAllHistory())
      await backend.set('history/' + h.id, { entry: h, deleted: false, updated_at: Date.now() });
    await setSetting('sync_migrated', true);
  }

  // ── lifecycle ──
  let unsubscribe = null;

  async function onUser(user) {
    if (user) {
      active = true;
      setStatus('syncing…');
      try {
        await migrateUp();
        unsubscribe = backend.subscribe(docs => { applyRemote(docs); });
        setStatus('✓ synced');
      } catch (e) {
        setStatus('⚠ sync error');
      }
    } else {
      active = false;
      if (unsubscribe) { unsubscribe(); unsubscribe = null; }
      setStatus(backend ? 'cloud sync off —' : '');
    }
  }

  function init() {
    if (window.__SYNC_BACKEND) {
      backend = window.__SYNC_BACKEND;
      backend.onAuth(onUser);
      return;
    }
    if (!window.FIREBASE_CONFIG || typeof firebase === 'undefined') {
      const row = document.getElementById('cloud-sync-row');
      if (row) row.style.display = 'none';
      return;
    }
    backend = makeFirebaseBackend(window.FIREBASE_CONFIG);
    backend.onAuth(onUser);
  }

  return {
    init, onLocalTxn, onLocalTxnDelete, onLocalSetting, onLocalHistory, onLocalHistoryDelete, withLock,
    signIn: () => backend && backend.signIn(),
    signOut: () => backend && backend.signOut(),
    toggle: () => (active ? Sync.signOut() : Sync.signIn())
  };
})();
