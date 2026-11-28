package com.yukitube.app

import android.annotation.SuppressLint
import android.content.Context
import android.content.MutableContextWrapper
import android.graphics.Bitmap
import android.net.Uri
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.View
import android.view.ViewGroup
import android.webkit.CookieManager
import android.webkit.RenderProcessGoneDetail
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.core.content.ContextCompat
import androidx.webkit.UserAgentMetadata
import androidx.webkit.WebSettingsCompat
import androidx.webkit.WebViewCompat
import androidx.webkit.WebViewFeature
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.withTimeout
import org.json.JSONObject
import java.io.ByteArrayInputStream
import java.util.concurrent.atomic.AtomicInteger

/**
 * The YouTube page that plays everything: a WebView the user does not see
 * (only in video mode), with the desktop's page bridge (agent-core.js) in
 * it. Commands go down with evaluateJavascript, the bridge's messages come
 * up through a message port that only www.youtube.com can use.
 */
class Engine(private val app: Context) {

    /** A WebView that keeps playing when the app is in the background:
     *  Chromium pauses a page's video when its window is hidden. */
    private class YukiWebView(ctx: Context) : WebView(ctx) {
        override fun onWindowVisibilityChanged(visibility: Int) {
            super.onWindowVisibilityChanged(View.VISIBLE)
        }
    }

    private val main = Handler(Looper.getMainLooper())
    private val reqIds = AtomicInteger(1)
    private val pending = HashMap<String, CompletableDeferred<JSONObject>>()
    /** Commands sent before the bridge was there; sent when it says hello. */
    private val waiting = ArrayList<String>()

    private val _state = MutableStateFlow(PlayerState())
    val state: StateFlow<PlayerState> = _state

    /** The bridge is in the page and answers. */
    private val _ready = MutableStateFlow(false)
    val ready: StateFlow<Boolean> = _ready

    /** The Google sign-in page is showing. */
    private val _signingIn = MutableStateFlow(false)
    val signingIn: StateFlow<Boolean> = _signingIn

    private var web: YukiWebView? = null
    private var host: ViewGroup? = null
    private val ctxWrapper = MutableContextWrapper(app)
    private var lastId = ""
    private var serviceOn = false

    private val earlyJs: String by lazy { app.assets.open("early.js").bufferedReader().readText() }
    private val agentJs: String by lazy {
        app.assets.open("agent-core.js").bufferedReader().readText() + "\n" +
            app.assets.open("glue.js").bufferedReader().readText()
    }

    // ------------------------------------------------------------- WebView

    /** Puts the page into the activity's holder (the activity decides where
     *  the holder is: behind the cover art, in video mode, full screen). */
    fun attach(holder: ViewGroup, activity: Context) {
        ctxWrapper.baseContext = activity
        val w = web ?: create()
        (w.parent as? ViewGroup)?.removeView(w)
        holder.addView(w, ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
        host = holder
    }

    fun detach(holder: ViewGroup) {
        if (host !== holder) return
        web?.let { holder.removeView(it) }
        host = null
        ctxWrapper.baseContext = app
    }

    @SuppressLint("SetJavaScriptEnabled", "RequiresFeature")
    private fun create(): YukiWebView {
        val w = YukiWebView(ctxWrapper)
        w.setBackgroundColor(0xFF000000.toInt())
        val s = w.settings
        s.javaScriptEnabled = true
        s.domStorageEnabled = true
        s.mediaPlaybackRequiresUserGesture = false
        s.cacheMode = WebSettings.LOAD_DEFAULT
        s.setSupportMultipleWindows(false)
        s.javaScriptCanOpenWindowsAutomatically = false
        // YouTube's desktop page: the bridge knows its player and its data.
        val chrome = Regex("Chrome/([\\d.]+)").find(s.userAgentString)?.groupValues?.get(1) ?: "131.0.0.0"
        val major = chrome.substringBefore(".")
        s.userAgentString = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) " +
            "Chrome/$major.0.0.0 Safari/537.36"
        if (WebViewFeature.isFeatureSupported(WebViewFeature.USER_AGENT_METADATA)) {
            // The same in the client hints: a desktop Chrome, not "Android WebView"
            // (Google's sign-in refuses WebViews that say they are one).
            WebSettingsCompat.setUserAgentMetadata(
                s,
                UserAgentMetadata.Builder()
                    .setBrandVersionList(
                        listOf(
                            UserAgentMetadata.BrandVersion.Builder().setBrand("Chromium").setMajorVersion(major).setFullVersion(chrome).build(),
                            UserAgentMetadata.BrandVersion.Builder().setBrand("Google Chrome").setMajorVersion(major).setFullVersion(chrome).build(),
                            UserAgentMetadata.BrandVersion.Builder().setBrand("Not_A Brand").setMajorVersion("24").setFullVersion("24.0.0.0").build(),
                        ),
                    )
                    .setFullVersion(chrome)
                    .setPlatform("Linux")
                    .setPlatformVersion("6.0.0")
                    .setArchitecture("x86")
                    .setBitness(64)
                    .setMobile(false)
                    .setModel("")
                    .build(),
            )
        }
        if (WebViewFeature.isFeatureSupported(WebViewFeature.REQUESTED_WITH_HEADER_ALLOW_LIST)) {
            WebSettingsCompat.setRequestedWithHeaderOriginAllowList(s, emptySet())
        }

        val cm = CookieManager.getInstance()
        cm.setAcceptCookie(true)
        cm.setAcceptThirdPartyCookies(w, true)
        acceptNoCookieBanner(cm)

        val origins = setOf("https://www.youtube.com")
        if (WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) {
            WebViewCompat.addWebMessageListener(w, "YukiAndroid", origins) { _, message, sourceOrigin, isMainFrame, _ ->
                if (isMainFrame && sourceOrigin.host == "www.youtube.com") message.data?.let { onUp(it) }
            }
        } else {
            Log.w(TAG, "no WEB_MESSAGE_LISTENER: the WebView is too old")
        }
        val startScripts = WebViewFeature.isFeatureSupported(WebViewFeature.DOCUMENT_START_SCRIPT)
        if (startScripts) {
            WebViewCompat.addDocumentStartJavaScript(w, earlyJs, origins)
            WebViewCompat.addDocumentStartJavaScript(w, agentJs, origins)
        }

        w.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val u = request.url
                if (u.scheme != "https" && u.scheme != "http") return true
                return !allowed(u)
            }

            override fun shouldInterceptRequest(view: WebView, request: WebResourceRequest): WebResourceResponse? {
                return if (isAd(request.url)) EMPTY() else null
            }

            override fun onPageStarted(view: WebView, url: String, favicon: Bitmap?) {
                if (url.startsWith("https://www.youtube.com/")) {
                    _ready.value = false
                    if (!startScripts) view.evaluateJavascript(earlyJs, null)
                }
            }

            override fun onPageFinished(view: WebView, url: String) {
                val u = Uri.parse(url)
                if (u.host == "www.youtube.com") {
                    if (!startScripts) view.evaluateJavascript(agentJs, null)
                    if (_signingIn.value) {
                        // Signed in: back to what was playing.
                        _signingIn.value = false
                        if (resume != null) view.loadUrl(resumeUrl())
                    }
                } else if (u.host == "consent.youtube.com" || u.host?.startsWith("consent.google") == true) {
                    // Cookie banner page despite the cookie: back to YouTube.
                    acceptNoCookieBanner(CookieManager.getInstance())
                    view.loadUrl(HOME)
                }
            }

            override fun onRenderProcessGone(view: WebView, detail: RenderProcessGoneDetail): Boolean {
                Log.w(TAG, "the page's renderer is gone; starting again")
                val parent = view.parent as? ViewGroup
                parent?.removeView(view)
                view.destroy()
                web = null
                _ready.value = false
                parent?.let { val n = create(); it.addView(n, ViewGroup.LayoutParams(-1, -1)) }
                return true
            }
        }
        w.webChromeClient = WebChromeClient()
        web = w
        w.loadUrl(HOME)
        return w
    }

    /** "Reject all" on YouTube's cookie banner, as a cookie (the EU shows the
     *  banner before anything plays). */
    private fun acceptNoCookieBanner(cm: CookieManager) {
        for (u in listOf("https://www.youtube.com", "https://youtube.com")) {
            cm.setCookie(u, "SOCS=CAI; Domain=.youtube.com; Path=/; Secure; Max-Age=34560000")
        }
        cm.flush()
    }

    private fun allowed(u: Uri): Boolean {
        val h = u.host ?: return false
        if (h == "youtube.com" || h.endsWith(".youtube.com")) return true
        // Google's sign-in and its country domains (accounts.google.ro…).
        if (_signingIn.value) return true
        return h.startsWith("accounts.google.") || h.endsWith(".google.com")
    }

    private fun isAd(u: Uri): Boolean {
        val h = u.host ?: return false
        val p = u.path ?: ""
        if (AD_HOSTS.any { h == it || h.endsWith(".$it") }) return true
        if (h.endsWith("youtube.com")) {
            return p.startsWith("/pagead/") || p.startsWith("/api/stats/ads") || p.startsWith("/ptracking") ||
                p.startsWith("/get_midroll_")
        }
        return false
    }

    // ------------------------------------------------------------ messages

    private fun onUp(text: String) {
        val m = try { JSONObject(text) } catch (e: Exception) { return }
        when (m.optString("type")) {
            "hello" -> {
                _ready.value = true
                val q = synchronized(waiting) { ArrayList(waiting).also { waiting.clear() } }
                q.forEach { down(it) }
            }
            "state" -> m.optJSONObject("state")?.let { onState(PlayerState.from(it)) }
            "bye" -> _ready.value = false
            else -> {
                val id = m.optString("reqId")
                if (id.isNotEmpty()) synchronized(pending) { pending.remove(id) }?.complete(m)
            }
        }
    }

    private fun onState(s: PlayerState) {
        _ready.value = true
        _state.value = s
        if (s.id.isNotEmpty() && s.id != lastId && !s.ad && s.title.isNotEmpty()) {
            lastId = s.id
            Prefs.played(Item(s.id, s.title, s.channel))
        }
        if (s.id.isNotEmpty() && !s.paused && !serviceOn) {
            serviceOn = true
            try {
                ContextCompat.startForegroundService(app, android.content.Intent(app, PlaybackService::class.java))
            } catch (e: Exception) {
                // Android refuses a foreground service started from the background.
                serviceOn = false
                Log.w(TAG, "playback service: $e")
            }
        }
    }

    fun serviceStopped() { serviceOn = false }

    private fun down(json: String) {
        main.post {
            web?.evaluateJavascript("window.__yukitubeAgent && window.__yukitubeAgent.handle($json)", null)
        }
    }

    /** A command for the player (play, pause, next, open…). */
    fun cmd(action: String, value: Any? = null) {
        val o = JSONObject().put("type", "cmd").put("action", action)
        if (value != null) o.put("value", value)
        val json = o.toString()
        if (_ready.value) down(json) else synchronized(waiting) {
            // Only the last of each kind: no pile of play/pause when it comes.
            waiting.removeAll { it.contains("\"action\":\"$action\"") }
            waiting.add(json)
        }
    }

    /** A command with an answer (search, recommend, playlists, queue…). */
    suspend fun request(action: String, value: Any? = null, timeoutMs: Long = 30000): JSONObject {
        val id = "a" + reqIds.getAndIncrement()
        val d = CompletableDeferred<JSONObject>()
        synchronized(pending) { pending[id] = d }
        val o = JSONObject().put("type", "cmd").put("action", action).put("reqId", id)
        if (value != null) o.put("value", value)
        val json = o.toString()
        if (_ready.value) down(json) else synchronized(waiting) { waiting.add(json) }
        try {
            return withTimeout(timeoutMs) { d.await() }
        } finally {
            synchronized(pending) { pending.remove(id) }
        }
    }

    fun play(it: Item) {
        if (it.list.isNotEmpty()) {
            cmd("openList", JSONObject().put("list", it.list).put("id", it.id))
        } else {
            cmd("open", JSONObject().put("id", it.id))
        }
        // Show it straight away; the page confirms in a moment.
        _state.value = _state.value.copy(id = it.id.ifEmpty { _state.value.id }, title = it.title, channel = it.channel,
            time = 0.0, duration = 0.0, paused = false, at = System.currentTimeMillis())
    }

    fun playInList(list: String, it: Item, index: Int) {
        cmd("openList", JSONObject().put("list", list).put("id", it.id).put("index", index))
        _state.value = _state.value.copy(id = it.id, title = it.title, channel = it.channel, time = 0.0, duration = 0.0,
            paused = false, at = System.currentTimeMillis())
    }

    /** Optimistic local change, so the button reacts at once. */
    fun toggle() {
        cmd("toggle")
        val s = _state.value
        _state.value = s.copy(paused = !s.paused, time = s.timeNow(), at = System.currentTimeMillis())
    }

    fun seek(t: Double) {
        cmd("seek", t)
        _state.value = _state.value.copy(time = t, at = System.currentTimeMillis())
    }

    // ---------------------------------------------------------- the account

    /** What played before the sign-in page took the WebView: played again after. */
    private var resume: PlayerState? = null

    private fun resumeUrl(): String {
        val r = resume ?: return HOME
        resume = null
        if (r.id.isEmpty()) return HOME
        return "https://www.youtube.com/watch?v=" + Uri.encode(r.id) + "&t=" + r.timeNow().toInt() + "s" +
            (if (r.list.isNotEmpty()) "&list=" + Uri.encode(r.list) else "")
    }

    fun signIn() {
        if (!_signingIn.value) resume = _state.value.takeIf { it.id.isNotEmpty() }
        _signingIn.value = true
        main.post {
            web?.loadUrl("https://accounts.google.com/ServiceLogin?service=youtube&hl=" +
                java.util.Locale.getDefault().language + "&continue=" + Uri.encode("https://www.youtube.com/signin?action_handle_signin=true&next=%2F"))
        }
    }

    fun cancelSignIn() {
        _signingIn.value = false
        val url = resumeUrl()
        main.post { web?.loadUrl(url) }
    }

    fun signOut() {
        val cm = CookieManager.getInstance()
        cm.removeAllCookies {
            acceptNoCookieBanner(cm)
            main.post { web?.loadUrl(HOME) }
        }
        _state.value = PlayerState()
    }

    /** Quit: stop the page (the activity and the service end themselves). */
    fun stopAll() {
        cmd("pause")
        main.post {
            web?.evaluateJavascript("document.querySelectorAll('video').forEach(v=>v.pause())", null)
        }
    }

    companion object {
        const val TAG = "YukiTube"
        const val HOME = "https://www.youtube.com/"
        private val AD_HOSTS = listOf(
            "doubleclick.net", "googlesyndication.com", "googleadservices.com", "googletagservices.com",
            "imasdk.googleapis.com", "pubads.g.doubleclick.net", "ad.youtube.com", "ads.youtube.com",
        )

        @Suppress("FunctionName")
        private fun EMPTY() = WebResourceResponse("text/plain", "utf-8", ByteArrayInputStream(ByteArray(0)))
    }
}
