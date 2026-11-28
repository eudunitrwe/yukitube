package com.yukitube.app

import android.content.Context
import android.content.SharedPreferences
import org.json.JSONArray
import org.json.JSONObject

/** Small settings and the list of what was played lately (the seeds of the
 *  recommendations, like on the desktop). */
object Prefs {
    private lateinit var sp: SharedPreferences

    fun init(ctx: Context) {
        sp = ctx.getSharedPreferences("yukitube", Context.MODE_PRIVATE)
    }

    var skin: String
        get() = sp.getString("skin", "retrowave") ?: "retrowave"
        set(v) = sp.edit().putString("skin", v).apply()

    var lastUpdateCheck: Long
        get() = sp.getLong("update_check", 0)
        set(v) = sp.edit().putLong("update_check", v).apply()

    /** The songs played lately, newest first. */
    fun recent(): List<Item> {
        val a = try { JSONArray(sp.getString("recent", "[]")) } catch (e: Exception) { JSONArray() }
        return (0 until a.length()).mapNotNull { Item.from(a.optJSONObject(it)) }
    }

    fun played(it: Item) {
        if (it.id.isEmpty()) return
        val list = listOf(it) + recent().filter { x -> x.id != it.id }
        val a = JSONArray()
        list.take(30).forEach { x ->
            a.put(JSONObject().put("id", x.id).put("title", x.title).put("channel", x.channel))
        }
        sp.edit().putString("recent", a.toString()).apply()
    }
}
