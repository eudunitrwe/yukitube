/* YukiTube for Android: the page bridge (agent-core.js, the same as on the
 * desktop) talks to the app through the YukiAndroid message port. */
(() => {
  if (window.__yukitubeGlue) return;
  window.__yukitubeGlue = true;
  let tries = 0;
  const start = () => {
    if (window.__yukitubeAgent || typeof YukiAndroid === "undefined") return;
    // YouTube's own objects (ytcfg, the player API) come a little later.
    if (typeof window.ytcfg === "undefined" && tries++ < 40) { setTimeout(start, 250); return; }
    const up = (msg) => { try { YukiAndroid.postMessage(JSON.stringify(msg)); } catch (e) {} };
    const agent = createYukiAgent(up, null);
    window.__yukitubeAgent = agent;
    document.documentElement.dataset.yukitubeAgent = "android";
    up(agent.hello());
    agent.push(true);
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => setTimeout(start, 200));
  else setTimeout(start, 200);
})();
