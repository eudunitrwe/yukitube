/* YukiTube bridge agent — runs inside the YouTube page.
 * Reads the player state and executes commands sent by the YukiTube remote.
 * Shared by the browser extension and the userscript. */
function createYukiAgent(send) {
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

  function navigate(id, t, list, index) {
    const url = "/watch?v=" + encodeURIComponent(id) + (t ? "&t=" + Math.floor(t) + "s" : "") +
      (list ? "&list=" + encodeURIComponent(list) + (index ? "&index=" + (index + 1) : "") : "");
    const watchEndpoint = { videoId: id };
    if (list) { watchEndpoint.playlistId = list; if (index) watchEndpoint.index = index; }
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
                watchEndpoint,
              },
            },
          })));
          // if the SPA navigation did not happen, fall back to a full load
          setTimeout(() => {
            if (videoId() !== id || (list && new URL(location.href).searchParams.get("list") !== list)) location.href = url;
          }, 2500);
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
      items = await pageVideos("/results?search_query=" + encodeURIComponent(q) + "&sp=EgIQAQ%253D%253D", 25);
    } catch (e) { error = String(e && e.message || e); }
    send({ type: "search_results", reqId, items, error });
  }

  // Videos from a YouTube page's ytInitialData: search results, the home
  // feed, related videos. Both layouts (videoRenderer, lockupViewModel);
  // ads and Shorts are left out.
  const SKIP = new Set(["adSlotRenderer", "promotedSparklesWebRenderer", "reelShelfRenderer", "richShelfRenderer",
    "shortsLockupViewModel", "reelItemRenderer"]);
  function videosIn(data, limit) {
    const items = [], seen = new Set();
    const txt = (n) => !n ? "" : n.simpleText || (n.runs || []).map((x) => x.text).join("");
    const first = (n, key) => {
      if (!n || typeof n !== "object") return null;
      if (!Array.isArray(n) && key in n) return n[key];
      for (const k in n) { const r = first(n[k], key); if (r) return r; }
      return null;
    };
    const add = (it) => { if (it.id && !seen.has(it.id)) { seen.add(it.id); items.push(it); } };
    const walk = (n) => {
      if (items.length >= limit || !n || typeof n !== "object") return;
      if (Array.isArray(n)) { n.forEach(walk); return; }
      const vr = n.videoRenderer || n.compactVideoRenderer || n.playlistVideoRenderer;
      if (vr && vr.videoId) {
        add({
          id: vr.videoId,
          title: txt(vr.title),
          channel: txt(vr.ownerText || vr.longBylineText || vr.shortBylineText),
          duration: txt(vr.lengthText) || (vr.badges ? "LIVE" : ""),
          views: txt(vr.shortViewCountText || vr.viewCountText),
        });
        return;
      }
      const lv = n.lockupViewModel;
      if (lv) {
        if (lv.contentType === "LOCKUP_CONTENT_TYPE_VIDEO" && lv.contentId) {
          const md = (lv.metadata && lv.metadata.lockupMetadataViewModel) || {};
          const rows = (md.metadata && md.metadata.contentMetadataViewModel &&
            md.metadata.contentMetadataViewModel.metadataRows) || [];
          const part = (r) => (rows[r] && rows[r].metadataParts && rows[r].metadataParts[0] &&
            rows[r].metadataParts[0].text && rows[r].metadataParts[0].text.content) || "";
          const badge = first(lv.contentImage, "thumbnailBadgeViewModel") || {};
          add({ id: lv.contentId, title: (md.title && md.title.content) || "", channel: part(0),
            duration: badge.text || "", views: part(1) });
        }
        return;
      }
      for (const k in n) if (!SKIP.has(k)) walk(n[k]);
    };
    walk(data);
    return items;
  }

  async function pageVideos(path, limit) {
    const r = await fetch(path, { credentials: "include" });
    const html = await r.text();
    const m = html.match(/(?:var ytInitialData|window\["ytInitialData"\])\s*=\s*(\{.+?\});\s*<\/script>/s);
    if (!m) throw new Error("no data");
    return videosIn(JSON.parse(m[1]), limit);
  }

  // YouTube's "Music" tab on the home page, for the signed-in account: music
  // only, picked from what the account listens to. The tab's name is in the
  // account's language.
  const MUSIC = /^(music|muzic[aă]|музыка|музика|musik|musique|m[uú]sica|muziek|muzyka|hudba|zene|musiikki|μουσική|müzik)$/i;
  const cfg = (k) => { try { return pageWin.ytcfg.get(k); } catch (e) { return undefined; } };
  const plain = (o) => o === undefined ? undefined : JSON.parse((pageWin.JSON || JSON).stringify(o));

  function musicChipToken(data) {
    let token = "";
    const txt = (n) => !n ? "" : typeof n === "string" ? n : n.simpleText || n.content ||
      (n.runs || []).map((x) => x.text).join("");
    const tokenIn = (n) => {
      if (!n || typeof n !== "object" || token) return "";
      if (n.continuationCommand && n.continuationCommand.token) return n.continuationCommand.token;
      for (const k in n) { const t = tokenIn(n[k]); if (t) return t; }
      return "";
    };
    const walk = (n) => {
      if (token || !n || typeof n !== "object") return;
      if (Array.isArray(n)) { n.forEach(walk); return; }
      for (const k in n) {
        const v = n[k];
        if (/chip/i.test(k) && v && typeof v === "object" && !Array.isArray(v) && MUSIC.test(txt(v.text).trim())) {
          token = tokenIn(v);
          if (token) return;
        }
        walk(v);
      }
    };
    walk(data);
    return token;
  }

  // The Authorization header YouTube's own requests carry when signed in.
  async function authHeader() {
    const m = document.cookie.match(/(?:^|;\s*)(?:SAPISID|__Secure-3PAPISID)=([^;]+)/);
    if (!m) return "";
    const ts = Math.floor(Date.now() / 1000);
    const buf = await crypto.subtle.digest("SHA-1", new TextEncoder().encode(ts + " " + m[1] + " " + location.origin));
    const hex = Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join("");
    return "SAPISIDHASH " + ts + "_" + hex;
  }

  async function pageData(path) {
    const r = await fetch(path, { credentials: "include" });
    const html = await r.text();
    const m = html.match(/(?:var ytInitialData|window\["ytInitialData"\])\s*=\s*(\{.+?\});\s*<\/script>/s);
    if (!m) throw new Error("no data");
    return JSON.parse(m[1]);
  }

  // A continuation of a page (the next rows of a feed or a playlist), as
  // YouTube's own scripts ask for it.
  async function browseMore(token) {
    const headers = {
      "Content-Type": "application/json",
      "X-Youtube-Client-Name": String(cfg("INNERTUBE_CONTEXT_CLIENT_NAME") || 1),
      "X-Youtube-Client-Version": String(cfg("INNERTUBE_CLIENT_VERSION") || ""),
      "X-Goog-AuthUser": String(cfg("SESSION_INDEX") || 0),
      "X-Origin": location.origin,
    };
    const auth = await authHeader();
    if (auth) headers.Authorization = auth;
    const key = cfg("INNERTUBE_API_KEY");
    const res = await fetch("/youtubei/v1/browse?prettyPrint=false" + (key ? "&key=" + encodeURIComponent(key) : ""), {
      method: "POST", credentials: "include", headers,
      body: JSON.stringify({ context: plain(cfg("INNERTUBE_CONTEXT")) || {}, continuation: token }),
    });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return res.json();
  }

  async function musicTabData() {
    const token = musicChipToken(await pageData("/"));
    if (!token) throw new Error("no Music tab");
    return browseMore(token);
  }

  async function musicTab(limit) {
    return videosIn(await musicTabData(), limit);
  }

  // The songs of a YouTube Mix (a watch page opened with list=RD<id>):
  // music like that one, personalised for the signed-in account.
  async function mixOf(id, limit) {
    const r = await fetch("/watch?v=" + encodeURIComponent(id) + "&list=RD" + encodeURIComponent(id),
      { credentials: "include" });
    const html = await r.text();
    const m = html.match(/(?:var ytInitialData|window\["ytInitialData"\])\s*=\s*(\{.+?\});\s*<\/script>/s);
    if (!m) return [];
    const out = [];
    const txt = (n) => !n ? "" : n.simpleText || (n.runs || []).map((x) => x.text).join("");
    const walk = (n) => {
      if (out.length >= limit || !n || typeof n !== "object") return;
      if (Array.isArray(n)) { n.forEach(walk); return; }
      const pv = n.playlistPanelVideoRenderer;
      if (pv && pv.videoId) {
        out.push({ id: pv.videoId, title: txt(pv.title), channel: txt(pv.shortBylineText || pv.longBylineText),
          duration: txt(pv.lengthText), views: "" });
        return;
      }
      for (const k in n) walk(n[k]);
    };
    walk(JSON.parse(m[1]));
    return out;
  }

  // Music for the signed-in account, fresh: the Mixes of what it listened to
  // lately (YouTube's watch history, newest first; the player's own
  // most-played as well), then YouTube's Music tab. What was just heard is
  // left out.
  async function recommend(reqId, val) {
    let items = [], error = "", recent = [];
    try {
      if (isMusic) throw new Error("recommendations only from www.youtube.com");
      try { recent = await pageVideos("/feed/history", 20); } catch (e) { recent = []; }
      const local = (val && Array.isArray(val.seeds)) ? val.seeds.map(String) : [];
      const seeds = [];
      for (const id of recent.map((v) => v.id).concat(local)) {
        if (seeds.length >= 4) break;
        if (!seeds.includes(id)) seeds.push(id);
      }
      const mixes = await Promise.all(seeds.map((id) => mixOf(id, 25).catch(() => [])));
      let tab = [];
      try { tab = await musicTab(30); } catch (e) { if (!seeds.length) throw e; }
      const heard = new Set(recent.map((v) => v.id).concat(seeds));
      const seen = new Set();
      const take = (v) => { if (v && v.id && !heard.has(v.id) && !seen.has(v.id)) { seen.add(v.id); items.push(v); } };
      for (let i = 0; i < 25; i++) mixes.forEach((mx) => take(mx[i]));
      tab.forEach(take);
      items = items.slice(0, 40);
    } catch (e) { error = String(e && e.message || e); }
    send({ type: "recommendations", reqId, items, error, loggedIn: account().loggedIn, fresh: recent.length > 0 });
  }

  // ------------------------------------------------------------ playlists
  // Playlists in a page's data: the newer lockups (playlists, albums, mixes)
  // and the older renderers. Each one: the list's id, its first video (for
  // the thumbnail and to start playing), title, owner, size.
  function listsIn(data, limit) {
    const items = [], seen = new Set();
    const txt = (n) => !n ? "" : typeof n === "string" ? n : n.simpleText || n.content ||
      (n.runs || []).map((x) => x.text).join("");
    const first = (n, key) => {
      if (!n || typeof n !== "object") return null;
      if (!Array.isArray(n) && key in n) return n[key];
      for (const k in n) { const r = first(n[k], key); if (r) return r; }
      return null;
    };
    const thumbId = (n) => {
      const m = JSON.stringify(n || {}).match(/\/vi\/([\w-]{11})\//);
      return m ? m[1] : "";
    };
    const add = (it) => {
      if (it.list && !seen.has(it.list) && items.length < limit) { seen.add(it.list); items.push(it); }
    };
    const walk = (n) => {
      if (items.length >= limit || !n || typeof n !== "object") return;
      if (Array.isArray(n)) { n.forEach(walk); return; }
      const lv = n.lockupViewModel;
      if (lv) {
        if (lv.contentType && lv.contentType !== "LOCKUP_CONTENT_TYPE_VIDEO" && lv.contentId &&
            !/^UC/.test(lv.contentId)) {
          const md = (lv.metadata && lv.metadata.lockupMetadataViewModel) || {};
          const rows = (md.metadata && md.metadata.contentMetadataViewModel &&
            md.metadata.contentMetadataViewModel.metadataRows) || [];
          const parts = (rows[0] && rows[0].metadataParts || []).map((p) => txt(p.text)).filter(Boolean);
          const we = first(lv.rendererContext, "watchEndpoint") || {};
          const badge = first(lv.contentImage, "thumbnailBadgeViewModel") || {};
          add({ list: lv.contentId, id: we.videoId || thumbId(lv.contentImage), title: txt(md.title),
            channel: parts.filter((p) => !/^(playlist|mix|album|podcast)$/i.test(p)).join(" · "),
            duration: badge.text || "", views: "" });
        }
        return;
      }
      const pr = n.playlistRenderer || n.gridPlaylistRenderer || n.radioRenderer || n.compactRadioRenderer ||
        n.compactPlaylistRenderer;
      if (pr && pr.playlistId) {
        const we = first(pr.navigationEndpoint, "watchEndpoint") || {};
        add({ list: pr.playlistId, id: we.videoId || thumbId(pr.thumbnail || pr.thumbnails), title: txt(pr.title),
          channel: txt(pr.shortBylineText || pr.longBylineText),
          duration: txt(pr.videoCountShortText || pr.videoCountText || pr.thumbnailText), views: "" });
        return;
      }
      for (const k in n) if (!SKIP.has(k) || k === "richShelfRenderer") walk(n[k]);
    };
    walk(data);
    return items;
  }

  function tokenIn(n) {
    if (!n || typeof n !== "object") return "";
    if (Array.isArray(n)) {
      for (const v of n) { const t = tokenIn(v); if (t) return t; }
      return "";
    }
    const c = n.continuationItemRenderer || n.continuationItemViewModel;
    if (c) {
      const m = JSON.stringify(c).match(/"continuationCommand":\{"token":"([^"]+)"/);
      return m ? m[1] : "";
    }
    for (const k in n) { const t = tokenIn(n[k]); if (t) return t; }
    return "";
  }

  // The account's own playlists (and the ones it saved), with Liked videos
  // and Watch later.
  async function myLists() {
    let data = await pageData("/feed/playlists");
    let items = listsIn(data, 200);
    for (let i = 0; i < 5 && items.length < 200; i++) {
      const tok = tokenIn(data);
      if (!tok) break;
      try { data = await browseMore(tok); } catch (e) { break; }
      const more = listsIn(data, 200);
      if (!more.length) break;
      items = items.concat(more.filter((x) => !items.some((y) => y.list === x.list)));
    }
    if (!items.length) items = listsIn(await pageData("/feed/library"), 200);
    for (const special of ["WL", "LL"]) {
      if (items.some((x) => x.list === special)) continue;
      let songs = [];
      try { songs = await playlistVideos(special, 1); } catch (e) {}
      if (songs.length) items.unshift({ list: special, id: songs[0].id, title: "", channel: "", duration: "", views: "" });
    }
    return items;
  }

  // Playlists YouTube picks: the mixes and playlists of the home page and of
  // its Music tab, "My Mix", the Mix of what was heard lately, and playlists
  // like the ones of the channels heard most.
  async function suggestedLists(val) {
    const signed = account().loggedIn;
    const seeds = ((val && val.seeds) || []).filter((x) => x && x.id);
    let recent = [];
    if (signed) { try { recent = await pageVideos("/feed/history", 10); } catch (e) {} }
    const pool = [];
    for (const v of recent.concat(seeds)) if (!pool.some((x) => x.id === v.id)) pool.push(v);
    const mixes = pool.slice(0, 6).map((v) => ({ list: "RD" + v.id, id: v.id,
      title: "Mix – " + (v.title || ""), channel: v.channel || "YouTube", duration: "Mix", views: "" }));
    const channels = [];
    for (const v of pool) {
      const c = (v.channel || "").replace(/\s*-\s*Topic$/i, "").replace(/VEVO$/i, "").trim();
      if (c && !channels.includes(c)) channels.push(c);
      if (channels.length >= 3) break;
    }
    const jobs = [
      pageData("/").then((d) => listsIn(d, 30)).catch(() => []),
      signed ? musicTabData().then((d) => listsIn(d, 30)).catch(() => []) : Promise.resolve([]),
      ...channels.map((c) => pageData("/results?search_query=" + encodeURIComponent(c) + "&sp=EgIQAw%253D%253D")
        .then((d) => listsIn(d, 8)).catch(() => [])),
    ];
    const lists = await Promise.all(jobs);
    const out = [], seen = new Set();
    const take = (x) => { if (x && x.list && x.id && !seen.has(x.list)) { seen.add(x.list); out.push(x); } };
    for (let i = 0; i < 30; i++) {
      take(mixes[i]);
      lists.forEach((l) => take(l[i]));
    }
    return out.slice(0, 60);
  }

  // The videos of a playlist. A Mix has no playlist page: its videos are
  // the ones beside the player on its watch page.
  async function playlistVideos(list, limit, firstId) {
    if (/^RD/.test(list)) {
      const id = firstId || list.slice(2);
      const out = [];
      const txt = (n) => !n ? "" : n.simpleText || (n.runs || []).map((x) => x.text).join("");
      const walk = (n) => {
        if (out.length >= limit || !n || typeof n !== "object") return;
        if (Array.isArray(n)) { n.forEach(walk); return; }
        const pv = n.playlistPanelVideoRenderer;
        if (pv && pv.videoId) {
          out.push({ id: pv.videoId, title: txt(pv.title), channel: txt(pv.shortBylineText || pv.longBylineText),
            duration: txt(pv.lengthText), views: "" });
          return;
        }
        for (const k in n) walk(n[k]);
      };
      walk(await pageData("/watch?v=" + encodeURIComponent(id) + "&list=" + encodeURIComponent(list)));
      return out;
    }
    let data = await pageData("/playlist?list=" + encodeURIComponent(list));
    let items = videosIn(data, limit);
    for (let i = 0; i < 10 && items.length < limit; i++) {
      const tok = tokenIn(data);
      if (!tok) break;
      try { data = await browseMore(tok); } catch (e) { break; }
      const more = videosIn(data, limit).filter((x) => !items.some((y) => y.id === x.id));
      if (!more.length) break;
      items = items.concat(more);
    }
    return items.slice(0, limit);
  }

  async function playlists(reqId, val) {
    const kind = (val && val.kind) === "mine" ? "mine" : "suggested";
    let items = [], error = "";
    try {
      if (isMusic) throw new Error("playlists only from www.youtube.com");
      if (kind === "mine" && !account().loggedIn) throw new Error("signed out");
      items = kind === "mine" ? await myLists() : await suggestedLists(val);
    } catch (e) { error = String(e && e.message || e); }
    send({ type: "playlists", reqId, kind, items, error, loggedIn: account().loggedIn });
  }

  async function playlistItems(reqId, val) {
    let items = [], error = "";
    try {
      items = await playlistVideos(String(val.list), 200, val.id);
    } catch (e) { error = String(e && e.message || e); }
    send({ type: "playlist_items", reqId, list: val.list, items, error });
  }

  // Plays a playlist: from the given video, or from its first one.
  async function openList(val) {
    const list = String(val.list);
    let id = val.id ? String(val.id) : "";
    if (!id) {
      try { const v = await playlistVideos(list, 1); id = v.length ? v[0].id : ""; } catch (e) {}
    }
    if (!id && /^RD/.test(list)) id = list.slice(2);
    if (id) navigate(id, 0, list, Number(val.index) || 0);
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
      case "recommend": recommend(msg.reqId, val); return;
      case "playlists": playlists(msg.reqId, val); return;
      case "playlistItems": if (val && val.list) playlistItems(msg.reqId, val); return;
      case "openList": if (val && val.list) openList(val); break;
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
