/* Main-world glue: talks to the isolated content script via window.postMessage. */
(() => {
  if (window.__yukitubeAgent) return;
  const agent = createYukiAgent((msg) => window.postMessage({ __yukitube: "up", msg }, location.origin));
  window.__yukitubeAgent = agent;
  document.documentElement.dataset.yukitubeAgent = "ext"; // visible to userscripts in any world
  window.addEventListener("message", (e) => {
    if (e.source !== window || !e.data || e.data.__yukitube !== "down") return;
    agent.handle(e.data.msg);
  });
  window.postMessage({ __yukitube: "up", msg: agent.hello() }, location.origin);
})();
