/* Isolated-world relay: page agent <-> extension background. */
(() => {
  let port = null;
  let queue = [];
  function connect() {
    try {
      port = chrome.runtime.connect({ name: "neontube" });
    } catch (e) {
      port = null; // extension was reloaded/removed
      return;
    }
    port.onMessage.addListener((msg) => window.postMessage({ __neontube: "down", msg }, location.origin));
    port.onDisconnect.addListener(() => {
      port = null;
      setTimeout(connect, 1000); // the service worker was restarted
    });
    const q = queue; queue = [];
    q.forEach((m) => port.postMessage(m));
  }
  window.addEventListener("message", (e) => {
    if (e.source !== window || !e.data || e.data.__neontube !== "up") return;
    if (port) { try { port.postMessage(e.data.msg); return; } catch (err) { port = null; } }
    if (e.data.msg.type === "hello") queue.push(e.data.msg);
  });
  connect();
})();
