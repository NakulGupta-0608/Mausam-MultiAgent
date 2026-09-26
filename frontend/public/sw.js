// MausamAI - Web Push Service Worker
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = {
        title: 'MausamAI Atmospheric Alert',
        body: event.data.text(),
      };
    }
  }

  const title = data.title || 'MausamAI Weather Alert';
  const options = {
    body: data.body || 'Atmospheric update for your saved plan.',
    icon: data.icon || '/vite.svg',
    badge: data.badge || '/vite.svg',
    tag: data.tag || 'mausam-alert',
    renotify: true,
    requireInteraction: data.data?.severity === 'danger',
    data: data.data || {},
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const targetUrl = event.notification.data?.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      // Focus existing window if open
      for (let client of windowClients) {
        if (client.url && 'focus' in client) {
          if (targetUrl.startsWith('#') || targetUrl.includes('#')) {
            client.navigate(targetUrl);
          }
          return client.focus();
        }
      }
      // If no window is open, open new one
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
