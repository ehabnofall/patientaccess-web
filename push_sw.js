// Shows appointment reminders sent by the server (Web Push).
// Registered with scope /push/ so it never touches the app's own caching.

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));

self.addEventListener('push', (event) => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (_) { data = { body: event.data && event.data.text() }; }
  const title = data.title || 'بوابة المريض';
  event.waitUntil(self.registration.showNotification(title, {
    body: data.body || '',
    icon: '/icons/Icon-192.png',
    badge: '/icons/Icon-192.png',
    dir: 'rtl',
    lang: 'ar',
    tag: data.tag || undefined,
    data: { url: data.url || '/#/me' },
  }));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = new URL((event.notification.data && event.notification.data.url) || '/#/me', self.location.origin).href;
  event.waitUntil((async () => {
    const all = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const c of all) {
      if (c.url.startsWith(self.location.origin)) { await c.focus(); if ('navigate' in c) { try { await c.navigate(url); } catch (_) {} } return; }
    }
    await self.clients.openWindow(url);
  })());
});
