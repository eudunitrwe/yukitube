/* YukiTube for Android: runs first in every www.youtube.com page, before
 * YouTube's own scripts.
 * - The page always thinks it is visible, so playback goes on with the app
 *   in the background or the screen off.
 * - The ads are taken out of the player's data (what uBlock Origin's
 *   json-prune does on the desktop); an ad that still shows is skipped.
 * - No "Video paused. Continue watching?" (what YouTube NonStop does).
 * - The page shows only the player, filling the view. */
(() => {
  if (window.__yukiEarly) return;
  window.__yukiEarly = true;

  // ------------------------------------------------------------ visibility
  try {
    Object.defineProperty(Document.prototype, "hidden", { configurable: true, get: () => false });
    Object.defineProperty(Document.prototype, "webkitHidden", { configurable: true, get: () => false });
    Object.defineProperty(Document.prototype, "visibilityState", { configurable: true, get: () => "visible" });
    Object.defineProperty(Document.prototype, "webkitVisibilityState", { configurable: true, get: () => "visible" });
    Document.prototype.hasFocus = () => true;
  } catch (e) {}
  const stop = (e) => e.stopImmediatePropagation();
  for (const t of ["visibilitychange", "webkitvisibilitychange", "pagehide", "freeze"]) {
    document.addEventListener(t, stop, true);
    window.addEventListener(t, stop, true);
  }
  window.addEventListener("blur", stop, true);

  // ------------------------------------------------------------------- ads
  const AD_KEYS = ["adPlacements", "adSlots", "playerAds", "adBreakHeartbeatParams"];
  const prune = (o) => {
    if (!o || typeof o !== "object") return o;
    try {
      for (const k of AD_KEYS) if (k in o) delete o[k];
      if (o.playerResponse && typeof o.playerResponse === "object") prune(o.playerResponse);
      if (Array.isArray(o)) for (const x of o) if (x && x.playerResponse) prune(x.playerResponse);
    } catch (e) {}
    return o;
  };
  const parse = JSON.parse;
  JSON.parse = function () { return prune(parse.apply(this, arguments)); };
  const rjson = Response.prototype.json;
  Response.prototype.json = function () { return rjson.apply(this, arguments).then(prune); };
  let ipr;
  try {
    Object.defineProperty(window, "ytInitialPlayerResponse", {
      configurable: true, get: () => ipr, set: (v) => { ipr = prune(v); },
    });
  } catch (e) {}

  // An ad that got through: muted, at 16x, to its end, skipped.
  let adMuted = false;
  setInterval(() => {
    const p = document.getElementById("movie_player");
    const v = p && p.querySelector("video");
    if (!v) return;
    if (p.classList.contains("ad-showing")) {
      if (!v.muted) { v.muted = true; adMuted = true; }
      try { v.playbackRate = 16; } catch (e) {}
      if (isFinite(v.duration) && v.duration > 0.5) { try { v.currentTime = v.duration - 0.2; } catch (e) {} }
      const b = document.querySelector(".ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-skip-button-modern");
      if (b) b.click();
    } else if (adMuted) {
      adMuted = false;
      v.muted = false;
      try { if (v.playbackRate === 16) v.playbackRate = 1; } catch (e) {}
    }
  }, 250);

  // --------------------------------------------------- "continue watching?"
  // YouTube asks when it has not seen a click or key press for a long time;
  // it keeps the time of the last one in window._lact.
  setInterval(() => { try { window._lact = Date.now(); } catch (e) {} }, 30000);
  setInterval(() => {
    for (const d of document.querySelectorAll("yt-confirm-dialog-renderer, ytd-popup-container tp-yt-paper-dialog")) {
      if (d.offsetParent === null) continue;
      const b = d.querySelector("#confirm-button button, #confirm-button, yt-button-renderer[dialog-confirm] button");
      if (b) { b.click(); const v = document.querySelector("#movie_player video"); if (v && v.paused) v.play().catch(() => {}); }
    }
  }, 1000);

  // ------------------------------------------------------------ the player
  const css = `
    html, body, ytd-app { background: #000 !important; overflow: hidden !important; }
    #masthead-container, ytd-masthead, tp-yt-app-drawer, ytd-mini-guide-renderer, #guide,
    ytd-browse, ytd-search, #secondary, #below, #chat, ytd-merch-shelf-renderer,
    ytd-popup-container tp-yt-iron-dropdown, tp-yt-paper-toast, ytd-consent-bump-v2-lightbox,
    ytd-mealbar-promo-renderer, yt-mealbar-promo-renderer, #player-ads, ytd-banner-promo-renderer {
      display: none !important;
    }
    #movie_player {
      position: fixed !important; left: 0 !important; top: 0 !important;
      width: 100vw !important; height: 100vh !important; z-index: 2147483646 !important;
      background: #000 !important;
    }
    #movie_player .html5-video-container, #movie_player video.html5-main-video {
      width: 100vw !important; height: 100vh !important; left: 0 !important; top: 0 !important;
    }
    #movie_player video.html5-main-video { object-fit: contain !important; }
    .ytp-chrome-top, .ytp-chrome-bottom, .ytp-gradient-top, .ytp-gradient-bottom {
      opacity: 0 !important; pointer-events: none !important;
    }
    .ytp-pause-overlay, .ytp-ce-element, .ytp-paid-content-overlay, .iv-branding, .ytp-cards-teaser,
    .ytp-endscreen-content, .ytp-autonav-endscreen-countdown-overlay, .ytp-autonav-endscreen,
    .ytp-videowall-still, .ytp-suggested-action, .ytp-overlay-bottom-right, .ytp-bezel, .ytp-bezel-text-wrapper,
    .ytp-contextmenu, .ytp-tooltip, .ytp-large-play-button, .ytp-spinner, .ytp-ad-overlay-container {
      display: none !important;
    }`;
  const addCss = () => {
    if (document.getElementById("yukitube-css")) return;
    const s = document.createElement("style");
    s.id = "yukitube-css";
    s.textContent = css;
    (document.head || document.documentElement).appendChild(s);
  };
  if (document.documentElement) addCss();
  document.addEventListener("DOMContentLoaded", addCss);
  // YouTube sizes the video for its own layout: make it measure again.
  let lastW = 0, lastH = 0;
  setInterval(() => {
    const p = document.getElementById("movie_player");
    if (!p) return;
    if (innerWidth !== lastW || innerHeight !== lastH || p.clientWidth !== innerWidth) {
      lastW = innerWidth; lastH = innerHeight;
      try { if (typeof p.setSize === "function") p.setSize(innerWidth, innerHeight); } catch (e) {}
      window.dispatchEvent(new Event("resize"));
    }
  }, 1000);
})();
