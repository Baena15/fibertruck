/*
 * FiberTrack Service Worker
 * Estrategia: cache-first para assets de app shell, network-only para API.
 */
const CACHE_NAME = 'fibertrack-v1';
const PRECACHE_ASSETS = [
  '/',
  '/static/frontend/app.v9.js',
  '/static/frontend/manifest.json',
  '/static/frontend/icons/icon-192x192.png',
  '/static/frontend/icons/icon-512x512.png',
  'https://unpkg.com/react@18/umd/react.production.min.js',
  'https://unpkg.com/react-dom@18/umd/react-dom.production.min.js',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://cdn.tailwindcss.com/'
];

self.addEventListener('install', function(event) {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(PRECACHE_ASSETS).catch(function(err) {
        console.warn('FiberTrack SW: algunos assets no se precachearon', err);
      });
    })
  );
});

self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(function(key) { return key !== CACHE_NAME; })
            .map(function(key) { return caches.delete(key); })
      );
    }).then(function() { return self.clients.claim(); })
  );
});

self.addEventListener('message', function(event) {
  if (event.data && event.data.type === 'GET_CACHE_STATUS') {
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.keys().then(function(requests) {
        event.ports[0].postMessage({
          cache: CACHE_NAME,
          count: requests.length,
          urls: requests.map(function(r) { return r.url; })
        });
      });
    });
  }
});

function isApiRequest(url) {
  return url.pathname.startsWith('/api/');
}

function matchCache(cache, request) {
  return cache.match(request).then(function(response) {
    if (response) return response;
    // Fallback: match by pathname
    var url = new URL(request.url);
    return cache.match(url.pathname);
  });
}

self.addEventListener('fetch', function(event) {
  const request = event.request;
  const url = new URL(request.url);

  // API: siempre red
  if (isApiRequest(url)) {
    event.respondWith(
      fetch(request).catch(function() {
        return new Response(JSON.stringify({error: 'Sin conexion'}), {
          status: 503,
          headers: {'Content-Type': 'application/json'}
        });
      })
    );
    return;
  }

  // Solo GET
  if (request.method !== 'GET') return;

  event.respondWith(
    caches.open(CACHE_NAME).then(function(cache) {
      return matchCache(cache, request).then(function(cached) {
        if (cached) {
          // Refrescar en segundo plano
          fetch(request).then(function(response) {
            if (response && response.ok) {
              cache.put(request, response);
            }
          }).catch(function() {});
          return cached;
        }
        return fetch(request).then(function(response) {
          if (!response || response.status !== 200) {
            return response;
          }
          const responseToCache = response.clone();
          cache.put(request, responseToCache);
          return response;
        }).catch(function() {
          return matchCache(cache, new Request('/')).then(function(fallback) {
            return fallback || new Response('Sin conexion', {status: 503});
          });
        });
      });
    })
  );
});
