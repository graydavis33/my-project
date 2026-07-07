const CACHE_NAME = 'payday-checklist-v3';
const PRECACHE = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  '../styles/brand.css',
  './firebase-config.js',
  './sync.js',
  './lib/firebase-app-compat.js',
  './lib/firebase-auth-compat.js',
  './lib/firebase-firestore-compat.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      Promise.allSettled(PRECACHE.map((url) => cache.add(url)))
    )
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Only handle the app's own assets. Everything else (Firestore/auth RPCs,
  // test backends, other origins) must pass straight to the network —
  // cache-first on live sync traffic would freeze it.
  if (url.origin !== self.location.origin) return;
  if (!url.pathname.includes('/payday-checklist/') && !url.pathname.includes('/styles/')) return;

  // expenses.json + page navigations: network first, cache fallback (fresh data when online)
  const networkFirst = request.mode === 'navigate' || url.pathname.endsWith('expenses.json');

  if (networkFirst) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response && response.status === 200) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() =>
          caches.match(request).then((cached) => cached || caches.match('./index.html'))
        )
    );
  } else {
    // Assets: cache first, network fallback (and backfill the cache)
    event.respondWith(
      caches.match(request).then(
        (cached) =>
          cached ||
          fetch(request).then((response) => {
            if (response && response.status === 200) {
              const copy = response.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
            }
            return response;
          })
      )
    );
  }
});
