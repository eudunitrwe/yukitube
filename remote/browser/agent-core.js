/* YukiTube bridge agent — runs inside the YouTube page.
 * Reads the player state and executes commands sent by the YukiTube remote.
 * Shared by the browser extension and the userscript. */
function createNeonAgent(send) {
  "use strict";
  const isMusic = location.hostname === "music.youtube.com";
  // Inside a userscript manager's sandbox (Violentmonkey in Firefox), the
  // page's own objects (the player API, ytcfg) are reachable only through
  // unsafeWindow. YouTube ignores scripted video.play()/pause() and clicks,
  // so the player API is the only reliable way to control it.
  const pageWin =
    (typeof unsafeWindow !== "undefined" && unsafeWindow) || window.wrappedJSObject || window;
  // Objects handed to the page must be built in the page's own world, or it
  // cannot read them.
  const toPage = (o) => (pageWin !== window && pageWin.JSON ? pageWin.JSON.parse(JSON.stringify(o)) : o);
  // true when YouTube's own JS objects are reachable.
  const mainWorld = typeof pageWin.ytcfg !== "undefined";
  const $ = (s) => document.querySelector(s);
  const player = () => pageWin.document.getElementById("movie_player");
  const video = () =>
    document.querySelector("#movie_player video") ||
    document.querySelector("video.html5-main-video") ||
    document.querySelector("video");
  const visible = (el) => !!el && el.offsetParent !== null && getComputedStyle(el).display !== "none";
  const call = (fn, ...a) => {
    const p = player();
    try { if (p && typeof p[fn] === "function") return { ok: true, v: p[fn](...a) }; } catch (e) {}
    return { ok: false };
  };

  let lastPlayed = 0;
  let lastSig = "";
  let lastSent = 0;

  function videoId() {
    const d = call("getVideoData");
    if (d.ok && d.v && d.v.video_id) return d.v.video_id;
    const u = new URL(location.href);
    if (u.searchParams.get("v")) return u.searchParams.get("v");
    const m = location.pathname.match(/^\/(?:shorts|live)\/([\w-]{6,})/);
    return m ? m[1] : "";
  }

  function meta() {
    let title = "", author = "", art = "";
    const d = call("getVideoData");
    if (d.ok && d.v) { title = d.v.title || ""; author = d.v.author || ""; }
    try {
      const ms = navigator.mediaSession && navigator.mediaSession.metadata;
      if (ms) {
        if (!title) title = ms.title || "";
        if (!author) author = ms.artist || "";
        if (ms.artwork && ms.artwork.length) art = ms.artwork[ms.artwork.length - 1].src || "";
      }
    } catch (e) {}
    if (!title) title = document.title.replace(/^\(\d+\)\s*/, "").replace(/\s*-\s*YouTube( Music)?$/, "");
    return { title, author, art };
  }

  function likeButton() {
    return (
      $("ytd-watch-metadata like-button-view-model button") ||
      $("#segmented-like-button button") ||
      $("ytd-menu-renderer #top-level-buttons-computed button[aria-pressed]") ||
      $("ytmusic-like-button-renderer #button-shape-like button") ||
      $("ytmusic-like-button-renderer .like")
    );
  }

  // Whether YouTube is signed in to a Google account (null: cannot tell
  // yet), and the account's avatar for the remote's account button.
  function account() {
    let loggedIn = null;
    try {
      const v = pageWin.ytcfg && typeof pageWin.ytcfg.get === "function" ? pageWin.ytcfg.get("LOGGED_IN") : undefined;
      if (typeof v === "boolean") loggedIn = v;
    } catch (e) {}
    const avatar = $("#avatar-btn img, ytmusic-settings-button img, ytd-topbar-menu-button-renderer img#img");
    if (loggedIn === null) {
      if (avatar) loggedIn = true;
      else if ($('a[href*="accounts.google.com/ServiceLogin"], a[href*="accounts.google.com/v3/signin"]')) loggedIn = false;
    }
    return { loggedIn, avatar: loggedIn && avatar && /^https:/.test(avatar.src || "") ? avatar.src : "" };
  }

  function state() {
    const v = video();
    const m = meta();
    const id = videoId();
    let volume = 100, muted = false;
    const gv = call("getVolume"), gm = call("isMuted");
    if (gv.ok && typeof gv.v === "number") volume = gv.v; else if (v) volume = Math.round(v.volume * 100);
    if (gm.ok && typeof gm.v === "boolean") muted = gm.v; else if (v) muted = v.muted;
    const lb = likeButton();
    const nextBtn = $(".ytp-next-button");
    const prevBtn = $(".ytp-prev-button");
    const dur = v && isFinite(v.duration) ? v.duration : 0;
    const paused = v ? v.paused || v.ended : true;
    if (!paused) lastPlayed = Date.now();
    return {
      id,
      title: m.title,
      channel: m.author,
      art: m.art,
      duration: dur,
      time: v ? v.currentTime : 0,
      paused,
      hasVideo: !!v && !!id,
      volume,
      muted,
      rate: v ? v.playbackRate : 1,
      loop: v ? v.loop : false,
      ad: !!$("#movie_player.ad-showing"),
      liked: lb ? lb.getAttribute("aria-pressed") === "true" : null,
      hasNext: isMusic || visible(nextBtn) || !!id,
      hasPrev: visible(prevBtn),
      lastPlayed,
      account: account(),
      host: location.hostname,
      url: location.href,
      ua: navigator.userAgent,
      brands: ((navigator.userAgentData && navigator.userAgentData.brands) || []).map((b) => b.brand).join(","),
      brave: !!navigator.brave,
      world: mainWorld ? (pageWin !== window ? "sandbox+page" : "page") : "sandbox",
    };
  }

  function push(force) {
    const s = state();
    const sig = [s.id, s.title, s.paused, Math.floor(s.time), s.volume, s.muted, s.rate, s.loop, s.ad, s.liked, s.duration].join("|");
    const now = Date.now();
    if (force || sig !== lastSig || now - lastSent > 2500) {
      lastSig = sig;
      lastSent = now;
      send({ type: "state", state: s });
    }
  }

  function navigate(id, t) {
    const url = "/watch?v=" + encodeURIComponent(id) + (t ? "&t=" + Math.floor(t) + "s" : "");
    if (!isMusic && mainWorld) {
      const app = $("ytd-app");
      if (app) {
        try {
          const Ev = pageWin.CustomEvent || CustomEvent;
          app.dispatchEvent(new Ev("yt-navigate", toPage({
            bubbles: true,
            detail: {
              endpoint: {
                commandMetadata: { webCommandMetadata: { url, webPageType: "WEB_PAGE_TYPE_WATCH", rootVe: 3832 } },
                watchEndpoint: { videoId: id },
              },
            },
          })));
          // if the SPA navigation did not happen, fall back to a full load
          setTimeout(() => { if (videoId() !== id) location.href = url; }, 2500);
          return;
        } catch (e) {}
      }
    }
    location.href = url;
  }

  function play() { if (!call("playVideo").ok) { const v = video(); if (v) v.play().catch(() => {}); } }
  function pause() {
    if (!call("pauseVideo").ok) { const v = video(); if (v) v.pause(); }
    // YouTube NonStop (in YukiTube) holds back any pause that does not follow
    // a click or key press in the page, taking it for YouTube's "Continue
    // watching?" pause. A pause from the remote is the user's own, so finish
    // it with the original pause NonStop keeps as yns_pause.
    const pv = pageWin.document.querySelector("#movie_player video") || pageWin.document.querySelector("video");
    try { if (pv && !pv.paused && typeof pv.yns_pause === "function") pv.yns_pause(); } catch (e) {}
  }
  function seekTo(t) {
    const v = video();
    const d = v && isFinite(v.duration) ? v.duration : 1e9;
    t = Math.max(0, Math.min(t, d - 0.5));
    if (call("seekTo", t, true).ok || !v) return;
    // no player API (userscript sandbox): set the media element directly and
    // re-apply if YouTube's player snaps back (e.g. right after play()).
    v.currentTime = t;
    let tries = 0;
    const check = () => {
      const cur = video();
      if (!cur || tries++ > 4) return;
      if (Math.abs(cur.currentTime - t) > 3) cur.currentTime = t;
      if (tries < 5) setTimeout(check, 350);
    };
    setTimeout(check, 350);
  }
  function setVolume(n) {
    n = Math.max(0, Math.min(100, Math.round(n)));
    if (call("setVolume", n).ok) {
      if (n > 0) call("unMute");
    } else {
      const v = video();
      if (v) { v.volume = n / 100; if (n > 0) v.muted = false; }
    }
  }

  async function search(q, reqId) {
    let items = [], error = "";
    try {
      if (isMusic) throw new Error("search only from www.youtube.com");
      const r = await fetch("/results?search_query=" + encodeURIComponent(q) + "&sp=EgIQAQ%253D%253D", { credentials: "include" });
      const html = await r.text();
      const m = html.match(/var ytInitialData\s*=\s*(\{.+?\});\s*<\/script>/s);
      if (!m) throw new Error("no data");
      const txt = (n) => !n ? "" : n.simpleText || (n.runs || []).map((x) => x.text).join("");
      const walk = (n) => {
        if (items.length >= 25 || !n || typeof n !== "object") return;
        if (Array.isArray(n)) { n.forEach(walk); return; }
        const vr = n.videoRenderer;
        if (vr && vr.videoId) {
          items.push({
            id: vr.videoId,
            title: txt(vr.title),
            channel: txt(vr.ownerText || vr.longBylineText),
            duration: txt(vr.lengthText) || "LIVE",
            views: txt(vr.shortViewCountText || vr.viewCountText),
          });
          return;
        }
        for (const k in n) walk(n[k]);
      };
      walk(JSON.parse(m[1]));
    } catch (e) { error = String(e && e.message || e); }
    send({ type: "search_results", reqId, items, error });
  }

  function handle(msg) {
    if (!msg || msg.type !== "cmd") return;
    const v = video();
    const val = msg.value;
    switch (msg.action) {
      case "toggle": (v && !v.paused && !v.ended) ? pause() : play(); break;
      case "play": play(); break;
      case "pause": pause(); break;
      case "stop": pause(); seekTo(0); break;
      case "next": {
        const b = isMusic ? $(".next-button") : $(".ytp-next-button");
        if (b && (isMusic || visible(b))) b.click(); else call("nextVideo");
        break;
      }
      case "prev": {
        if (v && v.currentTime > 4) { seekTo(0); break; }
        const b = isMusic ? $(".previous-button") : $(".ytp-prev-button");
        if (b && (isMusic || visible(b))) b.click(); else history.back();
        break;
      }
      case "seek": seekTo(Number(val) || 0); break;
      case "seekRel": if (v) seekTo(v.currentTime + (Number(val) || 0)); break;
      case "volume": setVolume(Number(val)); break;
      case "mute": {
        const m = call("isMuted");
        const muted = m.ok ? m.v : v && v.muted;
        if (val === undefined ? muted : !val) { if (!call("unMute").ok && v) v.muted = false; }
        else { if (!call("mute").ok && v) v.muted = true; }
        break;
      }
      case "rate": if (!call("setPlaybackRate", Number(val)).ok && v) v.playbackRate = Number(val); break;
      case "loop": if (v) v.loop = val === undefined ? !v.loop : !!val; break;
      case "like": { const b = likeButton(); if (b) b.click(); break; }
      case "skipAd": {
        const b = $(".ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-skip-button-modern");
        if (b) b.click();
        break;
      }
      case "open": if (val && val.id) navigate(String(val.id), val.t); break;
      case "search": search(String(val || ""), msg.reqId); return;
      case "focus": window.focus(); break;
    }
    setTimeout(() => push(true), 120);
    setTimeout(() => push(true), 600);
  }

  setInterval(() => push(false), 500);
  document.addEventListener("play", () => push(true), true);
  document.addEventListener("pause", () => push(true), true);
  document.addEventListener("volumechange", () => push(true), true);
  document.addEventListener("yt-navigate-finish", () => setTimeout(() => push(true), 300));
  window.addEventListener("pagehide", () => send({ type: "bye" }));

  return { handle, push, hello: () => ({ type: "hello", host: location.hostname, ua: navigator.userAgent }) };
}
