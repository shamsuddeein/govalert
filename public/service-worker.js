/**
 * RecruitmentAlert: Progressive Web App Service Worker
 * Designed for low/mid-range Android devices, slow 3G networks, and high data efficiency.
 *
 * Strategies:
 * 1. Static Assets: Cache-First with versioned cache names.
 * 2. HTML Pages: Network-First with strict 3-second network timeout & Cache fallback.
 * 3. Offline Fallback: Serves /offline.html when network is unavailable and page is uncached.
 * 4. Web Push API: Receives and displays instant recruitment alerts.
 */

const VERSION = "v1.0.0";
const STATIC_CACHE = `govalert-static-${VERSION}`;
const PAGE_CACHE = `govalert-pages-${VERSION}`;
const OFFLINE_CACHE = `govalert-offline-${VERSION}`;
const MAX_PAGE_CACHE_SIZE = 50;

const STATIC_ASSETS = [
  "/",
  "/manifest.json",
  "/favicon.svg",
  "/icon-192x192.png",
  "/icon-512x512.png",
  "/icon-maskable.png",
  "/offline.html",
];

// Helper: Trim page cache to max items (LRU policy)
async function trimCache(cacheName, maxItems) {
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  if (keys.length > maxItems) {
    await cache.delete(keys[0]);
    await trimCache(cacheName, maxItems);
  }
}

// Installation: Pre-cache static shell & offline fallback
self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const offlineCache = await caches.open(OFFLINE_CACHE);
      await offlineCache.add(new Request("/offline.html", { cache: "reload" }));

      const staticCache = await caches.open(STATIC_CACHE);
      await staticCache.addAll(STATIC_ASSETS);

      await self.skipWaiting();
    })()
  );
});

// Activation: Clean up stale caches from previous deployments
self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames.map((cacheName) => {
          if (
            cacheName !== STATIC_CACHE &&
            cacheName !== PAGE_CACHE &&
            cacheName !== OFFLINE_CACHE
          ) {
            return caches.delete(cacheName);
          }
        })
      );
      await self.clients.claim();
    })()
  );
});

// Fetch Routing & Interception
self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Skip non-GET, API calls, or chrome-extension requests
  if (request.method !== "GET" || url.pathname.startsWith("/api/")) {
    return;
  }

  // 1. Static Assets (CSS, JS, Fonts, Images) -> Cache-First
  const isStaticAsset =
    STATIC_ASSETS.includes(url.pathname) ||
    /\.(js|css|png|jpg|jpeg|svg|webp|ico|woff2?)$/i.test(url.pathname);

  if (isStaticAsset) {
    event.respondWith(
      (async () => {
        const cached = await caches.match(request);
        if (cached) return cached;

        try {
          const response = await fetch(request);
          if (response && response.status === 200) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, response.clone());
          }
          return response;
        } catch (err) {
          return (await caches.match("/offline.html")) || Response.error();
        }
      })()
    );
    return;
  }

  // 2. Navigation / HTML Pages -> Network-First with 3-Second Timeout & Cache Fallback
  const isNavigation =
    request.mode === "navigate" ||
    (request.headers.get("accept") &&
      request.headers.get("accept").includes("text/html"));

  if (isNavigation) {
    event.respondWith(
      (async () => {
        // 3-second network race promise
        const networkFetch = new Promise((resolve, reject) => {
          const timeoutId = setTimeout(() => reject(new Error("Network timeout")), 3000);

          fetch(request)
            .then((response) => {
              clearTimeout(timeoutId);
              if (response && response.status === 200) {
                const responseClone = response.clone();
                caches.open(PAGE_CACHE).then((cache) => {
                  cache.put(request, responseClone);
                  trimCache(PAGE_CACHE, MAX_PAGE_CACHE_SIZE);
                });
              }
              resolve(response);
            })
            .catch((err) => {
              clearTimeout(timeoutId);
              reject(err);
            });
        });

        try {
          return await networkFetch;
        } catch (err) {
          // Network failed or timed out > 3s: serve cached copy or offline page
          const cachedPage = await caches.match(request);
          if (cachedPage) return cachedPage;

          // If home or jobs not in cache, fallback to offline.html
          const offlineFallback = await caches.match("/offline.html");
          if (offlineFallback) return offlineFallback;

          return new Response("Offline mode unavailable", {
            status: 503,
            headers: { "Content-Type": "text/plain" },
          });
        }
      })()
    );
    return;
  }
});

// Push Notifications Listener
self.addEventListener("push", (event) => {
  let data = {
    title: "New Verified Recruitment Alert",
    body: "A new federal government recruitment notice has been verified.",
    url: "/jobs",
    icon: "/icon-192x192.png",
  };

  if (event.data) {
    try {
      data = Object.assign(data, event.data.json());
    } catch (e) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: data.icon || "/icon-192x192.png",
    badge: "/icon-192x192.png",
    data: { url: data.url || "/jobs" },
    tag: data.tag || `job-alert-${Date.now()}`,
    renotify: true,
    vibrate: [100, 50, 100],
    actions: [
      { action: "explore", title: "View Listing" },
      { action: "close", title: "Dismiss" },
    ],
  };

  event.waitUntil(self.registration.showNotification(data.title, options));
});

// Notification Click Action
self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  if (event.action === "close") return;

  const targetUrl = event.notification.data?.url || "/jobs";

  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(targetUrl) && "focus" in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
