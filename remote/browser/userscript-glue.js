(() => {
  // Sent with every message: the remote only takes orders from bridges that
  // say which version they are.
  const BRIDGE = "1.6.0";
  const URL_HTTP = "http://127.0.0.1:8975/yt/up";
  const URL_FRAME = "http://127.0.0.1:8975/yt/frame";
  const URL_WS = "ws://127.0.0.1:8975";
  // The same key across reloads of this tab (sessionStorage is per tab), so
  // the remote keeps controlling it instead of a stale copy of the old page.
  let key = "";
  try { key = sessionStorage.getItem("yukitube-tab") || ""; } catch (e) {}
  if (!key) {
    key = "us-" + Math.random().toString(36).slice(2, 10);
    try { sessionStorage.setItem("yukitube-tab", key); } catch (e) {}
  }
  const gmx =
    typeof GM_xmlhttpRequest === "function" ? GM_xmlhttpRequest :
    typeof GM !== "undefined" && GM && typeof GM.xmlHttpRequest === "function" ? GM.xmlHttpRequest.bind(GM) : null;

  function start() {
    // The extension, or another copy of this bridge, already bridges this tab.
    const root = document.documentElement;
    if (root.dataset.yukitubeAgent === "ext" || root.dataset.yukitubeBridge) return;
    root.dataset.yukitubeBridge = BRIDGE;
    root.dataset.yukitubeAgent = "userscript";

    let out = [];
    let ws = null;
    const agent = createYukiAgent((msg) => {
      if (ws && ws.readyState === 1) {
        msg.tab = key; msg.agent = "userscript";
        ws.send(JSON.stringify(msg));
        return;
      }
      out.push(msg);
      if (out.length > 30) out = out.slice(-30);
    }, (jpeg, done) => {
      // Video frames go straight away, one at a time, not with the queue.
      if (ws && ws.readyState === 1) {
        if (ws.bufferedAmount < 1 << 20) ws.send(JSON.stringify({ type: "frame", tab: key, data: jpeg }));
        setTimeout(() => done(true), 0);
        return;
      }
      if (!gmx) { done(false); return; }
      gmx({
        method: "POST",
        url: URL_FRAME,
        headers: { "Content-Type": "text/plain", "X-YukiTube": "1", "X-Tab": key },
        data: jpeg,
        timeout: 4000,
        onload: (r) => { let j = null; try { j = JSON.parse(r.responseText); } catch (e) {} done(!j || j.more !== false); },
        onerror: () => done(true),
        ontimeout: () => done(true),
      });
    });

    if (gmx) {
      // HTTP through the userscript manager: not affected by the browser's
      // "local network access" restrictions for web pages.
      let busy = false, fails = 0, skip = 0;
      out.push(agent.hello());
      const done = () => { busy = false; };
      const pump = () => {
        if (busy) return;
        if (skip > 0) { skip--; return; }
        busy = true;
        const msgs = out; out = [];
        gmx({
          method: "POST",
          url: URL_HTTP,
          headers: { "Content-Type": "application/json", "X-YukiTube": "1" },
          data: JSON.stringify({ tab: key, agent: "userscript", bridge: BRIDGE, msgs }),
          timeout: 4000,
          onload: (r) => {
            done();
            if (fails > 0) { agent.push(true); out.unshift(agent.hello()); }
            fails = 0;
            let j = null;
            try { j = JSON.parse(r.responseText); } catch (e) {}
            if (j && Array.isArray(j.cmds)) j.cmds.forEach((c) => agent.handle(c));
          },
          onerror: () => { done(); fails++; skip = Math.min(10, fails); },
          ontimeout: () => { done(); fails++; skip = Math.min(10, fails); },
        });
      };
      setInterval(pump, 300);
      window.addEventListener("pagehide", () => { out.push({ type: "bye" }); pump(); });
      return;
    }

    // no GM API (@grant none managers): plain WebSocket from the page
    const connect = () => {
      try { ws = new WebSocket(URL_WS); } catch (e) { setTimeout(connect, 3000); return; }
      ws.onopen = () => {
        const h = agent.hello(); h.tab = key; h.agent = "userscript";
        ws.send(JSON.stringify(h));
        out = [];
        agent.push(true);
      };
      ws.onmessage = (e) => {
        let m; try { m = JSON.parse(e.data); } catch (err) { return; }
        if (m.type === "ping") { ws.send('{"type":"pong"}'); return; }
        if (m.tab === key) agent.handle(m);
      };
      ws.onclose = () => { ws = null; setTimeout(connect, 3000); };
    };
    connect();
  }

  setTimeout(start, 1500);
})();
