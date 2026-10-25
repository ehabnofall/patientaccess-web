// Small helper the app calls to turn phone notifications on or off.
// Results are plain strings so the Dart side stays simple.
(function () {
  function b64ToBytes(s) {
    const pad = '='.repeat((4 - (s.length % 4)) % 4);
    const raw = atob((s + pad).replace(/-/g, '+').replace(/_/g, '/'));
    return Uint8Array.from(raw, (c) => c.charCodeAt(0));
  }
  function supported() {
    return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
  }
  function iosNeedsInstall() {
    const ios = /iphone|ipad|ipod/i.test(navigator.userAgent);
    const standalone = window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
    return ios && !standalone;
  }
  async function reg() {
    return navigator.serviceWorker.register('/push_sw.js', { scope: '/push/' });
  }
  // Wait until the worker is running (the app page is outside its scope,
  // so navigator.serviceWorker.ready would never settle).
  function active(r) {
    if (r.active) return Promise.resolve();
    const w = r.installing || r.waiting;
    return new Promise((ok) => {
      if (!w) return ok();
      w.addEventListener('statechange', () => { if (w.state === 'activated') ok(); });
      setTimeout(ok, 8000);
    });
  }
  window.paPush = {
    // on | off | denied | unsupported | ios_install
    state: async function () {
      if (!supported()) return iosNeedsInstall() ? 'ios_install' : 'unsupported';
      if (Notification.permission === 'denied') return 'denied';
      try {
        const r = await navigator.serviceWorker.getRegistration('/push/');
        const s = r && (await r.pushManager.getSubscription());
        return s && Notification.permission === 'granted' ? 'on' : 'off';
      } catch (_) { return 'off'; }
    },
    // Returns the subscription as JSON text, or 'denied' / 'error:...'.
    enable: async function (vapidKey) {
      if (!supported()) return iosNeedsInstall() ? 'ios_install' : 'unsupported';
      const p = await Notification.requestPermission();
      if (p !== 'granted') return 'denied';
      try {
        const r = await reg();
        await active(r);
        let s = await r.pushManager.getSubscription();
        if (!s) s = await r.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64ToBytes(vapidKey) });
        return JSON.stringify(s.toJSON());
      } catch (e) { return 'error:' + (e && e.message ? e.message : e); }
    },
    // Returns the endpoint that was removed ('' when there was none).
    disable: async function () {
      try {
        const r = await navigator.serviceWorker.getRegistration('/push/');
        const s = r && (await r.pushManager.getSubscription());
        if (!s) return '';
        const ep = s.endpoint;
        await s.unsubscribe();
        return ep;
      } catch (_) { return ''; }
    },
  };
})();
