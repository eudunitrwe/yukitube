package com.yukitube.app

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.core.content.FileProvider
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest

/**
 * Updates from GitHub releases, like the desktop app: the release's
 * yukitube-<version>-android.apk, checked against its SHA256SUMS, then
 * handed to Android's installer.
 */
object Updater {
    private const val API = "https://api.github.com/repos/eudunitrwe/yukitube/releases/latest"

    data class Info(val version: String, val apk: String, val apkUrl: String, val sumsUrl: String, val size: Long)

    fun assetName(version: String) = "yukitube-$version-android.apk"

    /** The newer release, or null when this one is the latest. */
    suspend fun check(): Info? = withContext(Dispatchers.IO) {
        val j = JSONObject(get(API).decodeToString())
        val ver = j.optString("tag_name").trimStart('v', 'V')
        if (ver.isEmpty() || !newer(ver, BuildConfig.VERSION_NAME)) return@withContext null
        val assets = j.optJSONArray("assets") ?: return@withContext null
        var apk: JSONObject? = null
        var sums: JSONObject? = null
        for (i in 0 until assets.length()) {
            val a = assets.getJSONObject(i)
            when (a.optString("name")) {
                assetName(ver) -> apk = a
                "yukitube-$ver-SHA256SUMS" -> sums = a
            }
        }
        if (apk == null || sums == null) return@withContext null
        Info(ver, apk.getString("name"), apk.getString("browser_download_url"), sums.getString("browser_download_url"),
            apk.optLong("size"))
    }

    /** Downloads and checks the APK; returns the file. */
    suspend fun download(ctx: Context, info: Info, progress: (Int) -> Unit): File = withContext(Dispatchers.IO) {
        val sums = get(info.sumsUrl).decodeToString()
        val want = sums.lineSequence().map { it.trim().split(Regex("\\s+")) }
            .firstOrNull { it.size == 2 && it[1].trimStart('*') == info.apk }?.get(0)?.lowercase()
            ?: error("no checksum for ${info.apk}")
        val dir = File(ctx.cacheDir, "updates").apply { mkdirs() }
        dir.listFiles()?.forEach { it.delete() }
        val out = File(dir, info.apk)
        val md = MessageDigest.getInstance("SHA-256")
        val c = open(info.apkUrl)
        val total = c.contentLengthLong.takeIf { it > 0 } ?: info.size
        c.inputStream.use { inp ->
            out.outputStream().use { o ->
                val buf = ByteArray(64 * 1024)
                var done = 0L
                var lastPct = -1
                while (true) {
                    val n = inp.read(buf)
                    if (n < 0) break
                    o.write(buf, 0, n)
                    md.update(buf, 0, n)
                    done += n
                    val pct = if (total > 0) (done * 100 / total).toInt() else 0
                    if (pct != lastPct) { lastPct = pct; withContext(Dispatchers.Main) { progress(pct) } }
                }
            }
        }
        val got = md.digest().joinToString("") { "%02x".format(it) }
        if (got != want) { out.delete(); error("checksum mismatch") }
        out
    }

    /** Whether Android lets YukiTube install; if not, opens that setting. */
    fun canInstall(ctx: Context): Boolean {
        if (Build.VERSION.SDK_INT < 26 || ctx.packageManager.canRequestPackageInstalls()) return true
        ctx.startActivity(
            Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:" + ctx.packageName))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
        )
        return false
    }

    fun install(ctx: Context, apk: File) {
        val uri = FileProvider.getUriForFile(ctx, ctx.packageName + ".files", apk)
        ctx.startActivity(
            Intent(Intent.ACTION_VIEW).setDataAndType(uri, "application/vnd.android.package-archive")
                .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK),
        )
    }

    fun newer(a: String, b: String): Boolean {
        val x = a.split(".").map { it.toIntOrNull() ?: 0 }
        val y = b.split(".").map { it.toIntOrNull() ?: 0 }
        for (i in 0 until maxOf(x.size, y.size)) {
            val d = x.getOrElse(i) { 0 } - y.getOrElse(i) { 0 }
            if (d != 0) return d > 0
        }
        return false
    }

    private fun open(url: String): HttpURLConnection {
        val c = URL(url).openConnection() as HttpURLConnection
        c.connectTimeout = 15000
        c.readTimeout = 30000
        c.instanceFollowRedirects = true
        c.setRequestProperty("User-Agent", "YukiTube-Android/" + BuildConfig.VERSION_NAME)
        c.setRequestProperty("Accept", "application/vnd.github+json, */*")
        if (c.responseCode !in 200..299) error("HTTP ${c.responseCode}")
        return c
    }

    private fun get(url: String): ByteArray = open(url).inputStream.use { it.readBytes() }
}
