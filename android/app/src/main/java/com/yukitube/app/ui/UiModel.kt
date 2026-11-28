package com.yukitube.app.ui

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.yukitube.app.Engine
import com.yukitube.app.Item
import com.yukitube.app.Prefs
import com.yukitube.app.Updater
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject

sealed interface Load<out T> {
    data object Idle : Load<Nothing>
    data object Loading : Load<Nothing>
    data class Done<T>(val v: T) : Load<T>
    data class Failed(val msg: String) : Load<Nothing>
}

enum class Tab { HOME, SEARCH, LISTS, QUEUE, SETTINGS }

data class QueueData(val items: List<Item>, val index: Int, val list: String)

/** What the screen shows; it outlives the activity (the page plays on). */
class UiModel(private val engine: Engine) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    var tab by mutableStateOf(Tab.HOME)
    var videoMode by mutableStateOf(false)
    var fullScreen by mutableStateOf(false)
    var skin by mutableStateOf(skinOf(Prefs.skin))

    var recs by mutableStateOf<Load<List<Item>>>(Load.Idle)
    var query by mutableStateOf("")
    var results by mutableStateOf<Load<List<Item>>>(Load.Idle)
    var listsMine by mutableStateOf(false)
    var lists by mutableStateOf<Load<List<Item>>>(Load.Idle)
    var openedList by mutableStateOf<Item?>(null)
    var listItems by mutableStateOf<Load<List<Item>>>(Load.Idle)
    var queue by mutableStateOf<Load<QueueData>>(Load.Idle)

    var update by mutableStateOf<Updater.Info?>(null)
    var updateMsg by mutableStateOf("")
    var updateProgress by mutableStateOf(-1)
    var checking by mutableStateOf(false)

    private var searchJob: Job? = null

    fun chooseSkin(s: Skin) {
        skin = s
        Prefs.skin = s.key
    }

    private fun err(e: Throwable) = (e.message ?: e.javaClass.simpleName)

    private fun failed(o: JSONObject): String? = o.optString("error").takeIf { it.isNotEmpty() }

    fun loadRecs() {
        if (recs is Load.Loading) return
        recs = Load.Loading
        scope.launch {
            recs = try {
                val seeds = JSONArray().apply { Prefs.recent().take(6).forEach { put(it.id) } }
                val r = engine.request("recommend", JSONObject().put("seeds", seeds), 45000)
                var items = Item.list(r.optJSONArray("items"))
                if (items.isEmpty()) {
                    // Nothing heard yet and no Music tab in this region: music
                    // YouTube finds for "music", until there is something to go on.
                    val s = engine.request("search", "music mix")
                    items = Item.list(s.optJSONArray("items"))
                }
                if (items.isEmpty() && failed(r) != null) Load.Failed(failed(r)!!) else Load.Done(items)
            } catch (e: Throwable) { Load.Failed(err(e)) }
        }
    }

    fun search(q: String) {
        val text = q.trim()
        if (text.isEmpty()) return
        searchJob?.cancel()
        results = Load.Loading
        searchJob = scope.launch {
            results = try {
                val r = engine.request("search", text)
                val items = Item.list(r.optJSONArray("items"))
                if (items.isEmpty() && failed(r) != null) Load.Failed(failed(r)!!) else Load.Done(items)
            } catch (e: Throwable) { Load.Failed(err(e)) }
        }
    }

    fun loadLists(mine: Boolean) {
        listsMine = mine
        openedList = null
        lists = Load.Loading
        scope.launch {
            lists = try {
                val v = JSONObject().put("kind", if (mine) "mine" else "suggested")
                if (!mine) {
                    v.put("seeds", JSONArray().apply {
                        Prefs.recent().take(10).forEach {
                            put(JSONObject().put("id", it.id).put("title", it.title).put("channel", it.channel))
                        }
                    })
                }
                val r = engine.request("playlists", v, 45000)
                val items = Item.list(r.optJSONArray("items"))
                if (items.isEmpty() && failed(r) != null) Load.Failed(failed(r)!!) else Load.Done(items)
            } catch (e: Throwable) { Load.Failed(err(e)) }
        }
    }

    fun openList(pl: Item) {
        openedList = pl
        listItems = Load.Loading
        scope.launch {
            listItems = try {
                val r = engine.request("playlistItems", JSONObject().put("list", pl.list).put("id", pl.id), 45000)
                val items = Item.list(r.optJSONArray("items"))
                if (items.isEmpty() && failed(r) != null) Load.Failed(failed(r)!!) else Load.Done(items)
            } catch (e: Throwable) { Load.Failed(err(e)) }
        }
    }

    fun loadQueue() {
        queue = Load.Loading
        scope.launch {
            queue = try {
                val r = engine.request("queue")
                val items = Item.list(r.optJSONArray("items"))
                if (items.isEmpty() && failed(r) != null) Load.Failed(failed(r)!!)
                else Load.Done(QueueData(items, r.optInt("index", -1), r.optString("list")))
            } catch (e: Throwable) { Load.Failed(err(e)) }
        }
    }

    fun checkUpdate(quiet: Boolean) {
        if (checking) return
        checking = true
        if (!quiet) updateMsg = ""
        scope.launch {
            try {
                update = Updater.check()
                if (update == null && !quiet) updateMsg = "up_to_date"
                Prefs.lastUpdateCheck = System.currentTimeMillis()
            } catch (e: Throwable) {
                if (!quiet) updateMsg = "!" + err(e)
            } finally {
                checking = false
            }
        }
    }

    fun installUpdate(ctx: android.content.Context) {
        val info = update ?: return
        if (updateProgress >= 0) return
        if (!Updater.canInstall(ctx)) { updateMsg = "perm"; return }
        updateProgress = 0
        updateMsg = ""
        scope.launch {
            try {
                val f = Updater.download(ctx, info) { updateProgress = it }
                Updater.install(ctx, f)
            } catch (e: Throwable) {
                updateMsg = "!" + err(e)
            } finally {
                updateProgress = -1
            }
        }
    }
}
