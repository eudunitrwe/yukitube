package com.yukitube.app

import android.Manifest
import android.content.Intent
import android.content.pm.ActivityInfo
import android.content.pm.PackageManager
import android.graphics.Outline
import android.os.Build
import android.os.Bundle
import android.view.View
import android.view.ViewGroup
import android.view.ViewOutlineProvider
import android.widget.FrameLayout
import androidx.activity.OnBackPressedCallback
import androidx.activity.SystemBarStyle
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.platform.ComposeView
import androidx.core.content.ContextCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.yukitube.app.ui.Tab
import com.yukitube.app.ui.WebPlace
import com.yukitube.app.ui.YukiScreen
import com.yukitube.app.ui.YukiTheme
import org.json.JSONObject
import java.lang.ref.WeakReference

class MainActivity : AppCompatActivity() {
    private lateinit var root: FrameLayout
    private lateinit var holder: FrameLayout
    private val engine get() = YukiApp.engine
    private val ui get() = YukiApp.ui
    private var corner = 0f

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        current = WeakReference(this)

        root = FrameLayout(this)
        holder = FrameLayout(this).apply {
            outlineProvider = object : ViewOutlineProvider() {
                override fun getOutline(view: View, outline: Outline) {
                    outline.setRoundRect(0, 0, view.width, view.height, corner)
                }
            }
            clipToOutline = true
        }
        root.addView(holder, FrameLayout.LayoutParams(1, 1))
        val compose = ComposeView(this).apply {
            setContent {
                val skin = ui.skin
                LaunchedEffect(skin) { systemBars(skin.light, ui.fullScreen) }
                LaunchedEffect(Unit) {
                    snapshotFlow { ui.fullScreen }.collect { systemBars(ui.skin.light, it) }
                }
                YukiTheme(skin) { YukiScreen(ui, engine, ::placeWeb) }
            }
        }
        root.addView(compose, FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT))
        setContentView(root)
        engine.attach(holder, this)

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                when {
                    engine.signingIn.value -> engine.cancelSignIn()
                    ui.fullScreen -> ui.fullScreen = false
                    ui.tab == Tab.LISTS && ui.openedList != null -> ui.openedList = null
                    ui.tab != Tab.HOME -> ui.tab = Tab.HOME
                    // Like the home button: YukiTube plays on in the background.
                    else -> moveTaskToBack(true)
                }
            }
        })

        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1)
        }
        if (System.currentTimeMillis() - Prefs.lastUpdateCheck > 6 * 3600 * 1000L) ui.checkUpdate(quiet = true)
        handleShare(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleShare(intent)
    }

    override fun onDestroy() {
        engine.detach(holder)
        if (current?.get() === this) current = null
        super.onDestroy()
    }

    /** Where the page goes: behind the cover art, in the video box, full
     *  screen, or in front of everything for the Google sign-in. */
    private fun placeWeb(p: WebPlace) {
        val lp = holder.layoutParams as FrameLayout.LayoutParams
        val w = p.right - p.left
        val h = p.bottom - p.top
        if (lp.leftMargin != p.left || lp.topMargin != p.top || lp.width != w || lp.height != h) {
            lp.leftMargin = p.left
            lp.topMargin = p.top
            lp.width = maxOf(1, w)
            lp.height = maxOf(1, h)
            holder.layoutParams = lp
        }
        if (corner != p.corner) {
            corner = p.corner
            holder.invalidateOutline()
        }
        holder.translationZ = if (p.front) 10f else 0f
        if (p.front) holder.bringToFront() else if (root.indexOfChild(holder) != 0) {
            root.removeView(holder)
            root.addView(holder, 0, lp)
        }
    }

    private fun systemBars(light: Boolean, full: Boolean) {
        val c = WindowCompat.getInsetsController(window, window.decorView)
        c.isAppearanceLightStatusBars = light && !full
        c.isAppearanceLightNavigationBars = light && !full
        if (full) {
            c.systemBarsBehavior = WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
            c.hide(WindowInsetsCompat.Type.systemBars())
            requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE
        } else {
            c.show(WindowInsetsCompat.Type.systemBars())
            requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
        }
        enableEdgeToEdge(
            statusBarStyle = if (light) SystemBarStyle.light(0, 0) else SystemBarStyle.dark(0),
            navigationBarStyle = if (light) SystemBarStyle.light(0, 0) else SystemBarStyle.dark(0),
        )
    }

    /** A YouTube link shared to YukiTube: play it. */
    private fun handleShare(intent: Intent?) {
        if (intent?.action != Intent.ACTION_SEND) return
        val text = intent.getStringExtra(Intent.EXTRA_TEXT) ?: return
        val url = Regex("https?://\\S+").find(text)?.value ?: return
        val u = android.net.Uri.parse(url)
        val host = u.host ?: return
        val id = when {
            host.endsWith("youtu.be") -> u.pathSegments.firstOrNull()
            u.getQueryParameter("v") != null -> u.getQueryParameter("v")
            u.pathSegments.size >= 2 && u.pathSegments[0] in setOf("shorts", "live", "embed") -> u.pathSegments[1]
            else -> null
        } ?: ""
        val list = u.getQueryParameter("list") ?: ""
        if (id.isEmpty() && list.isEmpty()) return
        if (list.isNotEmpty()) engine.cmd("openList", JSONObject().put("list", list).put("id", id))
        else engine.play(Item(id, ""))
        intent.action = null
    }

    companion object {
        private var current: WeakReference<MainActivity>? = null
        fun finishAll() {
            current?.get()?.finishAndRemoveTask()
        }
    }
}
