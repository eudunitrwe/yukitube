package com.yukitube.app

import org.json.JSONArray
import org.json.JSONObject

/** A video, a song or a playlist, as the page bridge reports them. */
data class Item(
    val id: String,
    val title: String,
    val channel: String = "",
    val duration: String = "",
    val views: String = "",
    val list: String = "",
    val upNext: Boolean = false,
) {
    val thumb: String get() = if (id.isEmpty()) "" else "https://i.ytimg.com/vi/$id/mqdefault.jpg"

    companion object {
        fun from(o: JSONObject?): Item? {
            if (o == null) return null
            val id = o.optString("id")
            val list = o.optString("list")
            if (id.isEmpty() && list.isEmpty()) return null
            return Item(
                id = id,
                title = o.optString("title"),
                channel = o.optString("channel"),
                duration = o.optString("duration"),
                views = o.optString("views"),
                list = list,
                upNext = o.optBoolean("upNext"),
            )
        }

        fun list(a: JSONArray?): List<Item> =
            if (a == null) emptyList() else (0 until a.length()).mapNotNull { from(a.optJSONObject(it)) }
    }
}

/** What the player is doing (the bridge's "state" message). */
data class PlayerState(
    val id: String = "",
    val title: String = "",
    val channel: String = "",
    val art: String = "",
    val duration: Double = 0.0,
    val time: Double = 0.0,
    val paused: Boolean = true,
    val rate: Double = 1.0,
    val loop: Boolean = false,
    val ad: Boolean = false,
    val liked: Boolean? = null,
    val hasNext: Boolean = false,
    val loggedIn: Boolean? = null,
    val avatar: String = "",
    val next: Item? = null,
    val list: String = "",
    /** When this state was received (to move the time on between messages). */
    val at: Long = System.currentTimeMillis(),
) {
    val thumb: String
        get() = if (id.isEmpty()) "" else "https://i.ytimg.com/vi/$id/hqdefault.jpg"

    /** The position now, counting the time since the message while playing. */
    fun timeNow(): Double {
        if (paused || duration <= 0) return time
        return (time + (System.currentTimeMillis() - at) / 1000.0 * rate).coerceAtMost(duration)
    }

    companion object {
        fun from(o: JSONObject): PlayerState {
            val acc = o.optJSONObject("account")
            return PlayerState(
                id = o.optString("id"),
                // Without a video (YouTube's home page) the title is the page's.
                title = if (o.optString("id").isEmpty()) "" else o.optString("title"),
                channel = if (o.optString("id").isEmpty()) "" else o.optString("channel"),
                art = o.optString("art"),
                duration = o.optDouble("duration", 0.0).takeIf { !it.isNaN() } ?: 0.0,
                time = o.optDouble("time", 0.0).takeIf { !it.isNaN() } ?: 0.0,
                paused = o.optBoolean("paused", true),
                rate = o.optDouble("rate", 1.0).takeIf { !it.isNaN() } ?: 1.0,
                loop = o.optBoolean("loop"),
                ad = o.optBoolean("ad"),
                liked = if (o.isNull("liked") || !o.has("liked")) null else o.optBoolean("liked"),
                hasNext = o.optBoolean("hasNext"),
                loggedIn = if (acc == null || acc.isNull("loggedIn")) null else acc.optBoolean("loggedIn"),
                avatar = acc?.optString("avatar") ?: "",
                next = Item.from(o.optJSONObject("next")),
                list = o.optString("list"),
            )
        }
    }
}

fun fmtTime(s: Double): String {
    val t = s.toLong().coerceAtLeast(0)
    val h = t / 3600
    val m = (t % 3600) / 60
    val sec = t % 60
    return if (h > 0) "%d:%02d:%02d".format(h, m, sec) else "%d:%02d".format(m, sec)
}
