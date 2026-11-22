/* YukiTube bridge: keeps a WebSocket to the local YukiTube remote and routes
 * messages to/from every open YouTube tab. */
const WS_URL = "ws://127.0.0.1:8975";
const session = Math.random().toString(36).slice(2, 8);
const ports = new Map(); // key -> Port
let ws = null;
let retryTimer = null;

const keyFor = (tabId) => `ext-${session}-${tabId}`;

function wsSend(obj) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(obj));
    return true;
  }
  return false;
}

function scheduleRetry() {
  if (retryTimer) return;
  retryTimer = setTimeout(() => { retryTimer = null; connect(); }, 3000);
}

function connect() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;
  try {
    ws = new WebSocket(WS_URL);
  } catch (e) {
    ws = null;
    scheduleRetry();
    return;
  }
  ws.onopen = () => {
    wsSend({ type: "hello", agent: "extension", ua: navigator.userAgent, tabs: [...ports.keys()] });
    for (const [key, port] of ports) {
      wsSend({ type: "hello", tab: key, agent: "extension" });
      try { port.postMessage({ type: "cmd", action: "refresh" }); } catch (e) {}
    }
  };
  ws.onmessage = (ev) => {
    let msg;
    try { msg = JSON.parse(ev.data); } catch (e) { return; }
    if (msg.type === "ping") { wsSend({ type: "pong" }); return; }
    if (msg.type === "newtab") {
      chrome.tabs.create({ url: msg.url || "https://www.youtube.com/" });
      return;
    }
    if (msg.type === "cmd" && msg.action === "focus" && msg.tab) {
      const tabId = Number(String(msg.tab).split("-").pop());
      chrome.tabs.update(tabId, { active: true }).then((t) => chrome.windows.update(t.windowId, { focused: true })).catch(() => {});
      return;
    }
    const port = ports.get(msg.tab);
    if (port) { try { port.postMessage(msg); } catch (e) {} }
  };
  ws.onclose = () => { ws = null; scheduleRetry(); };
  ws.onerror = () => {};
}

chrome.runtime.onConnect.addListener((port) => {
  if (port.name !== "neontube" || !port.sender || !port.sender.tab) return;
  const key = keyFor(port.sender.tab.id);
  const old = ports.get(key);
  if (old && old !== port) { try { old.disconnect(); } catch (e) {} }
  ports.set(key, port);
  port.onMessage.addListener((msg) => {
    if (!msg || typeof msg !== "object") return;
    msg.tab = key;
    if (msg.type === "hello") msg.agent = "extension";
    if (!wsSend(msg)) connect();
  });
  port.onDisconnect.addListener(() => {
    if (ports.get(key) === port) {
      ports.delete(key);
      wsSend({ type: "bye", tab: key });
    }
  });
  connect();
});

// Wake up periodically so the bridge reconnects when the app is started later.
chrome.alarms.create("neontube-keepalive", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener(() => connect());
chrome.runtime.onStartup.addListener(connect);
chrome.runtime.onInstalled.addListener(connect);
connect();
