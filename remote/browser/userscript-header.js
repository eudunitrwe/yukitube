// ==UserScript==
// @name         YukiTube Bridge
// @namespace    neontube.local
// @version      1.5.0
// @description  Connects this YouTube tab to the YukiTube remote running on this computer (127.0.0.1:8975).
// @match        https://www.youtube.com/*
// @match        https://music.youtube.com/*
// @match        https://m.youtube.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM.xmlHttpRequest
// @grant        unsafeWindow
// @connect      127.0.0.1
// @connect      localhost
// @updateURL    http://127.0.0.1:8975/yukitube.user.js
// @downloadURL  http://127.0.0.1:8975/yukitube.user.js
// @run-at       document-idle
// @noframes
// ==/UserScript==
