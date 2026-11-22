/* Main-world glue: talks to the isolated content script via window.postMessage. */
(() => {
  if (window.__neontubeAgent) return;
  const agent = createNeonAgent((msg) => window.postMessage({ __neontube: "up", msg }, location.origin));
  window.__neontubeAgent = agent;
  document.documentElement.dataset.neontube = "ext"; // visible to userscripts in any world
  window.addEventListener("message", (e) => {
    if (e.source !== window || !e.data || e.data.__neontube !== "down") return;
    agent.handle(e.data.msg);
  });
  window.postMessage({ __neontube: "up", msg: agent.hello() }, location.origin);
})();
