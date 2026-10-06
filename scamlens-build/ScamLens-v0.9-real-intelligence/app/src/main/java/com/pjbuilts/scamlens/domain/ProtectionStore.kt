package com.pjbuilts.scamlens.domain

import android.content.Context
import android.util.Base64

class ProtectionStore(context: Context) {
    private val prefs = context.getSharedPreferences("scamlens_protection_v09", Context.MODE_PRIVATE)

    var autoBlockHighRisk: Boolean
        get() = prefs.getBoolean("auto_block_high", false)
        set(value) { prefs.edit().putBoolean("auto_block_high", value).apply() }

    var silenceHighRisk: Boolean
        get() = prefs.getBoolean("silence_high", false)
        set(value) { prefs.edit().putBoolean("silence_high", value).apply() }

    var liveUrlChecks: Boolean
        get() = prefs.getBoolean("live_url_checks", true)
        set(value) { prefs.edit().putBoolean("live_url_checks", value).apply() }

    var communityIntel: Boolean
        get() = prefs.getBoolean("community_intel", true)
        set(value) { prefs.edit().putBoolean("community_intel", value).apply() }

    var privacyRedaction: Boolean
        get() = prefs.getBoolean("privacy_redaction", true)
        set(value) { prefs.edit().putBoolean("privacy_redaction", value).apply() }

    fun reportCount(key: String): Int = prefs.getInt("report_${safeKey(key)}", 0)

    fun report(key: String): Int {
        val k = "report_${safeKey(key)}"
        val next = prefs.getInt(k, 0) + 1
        prefs.edit().putInt(k, next).apply()
        return next
    }

    fun communityReportCount(number: String): Int = prefs.getInt("community_${safeKey(number)}", 0)

    fun cacheCommunityReportCount(number: String, count: Int) {
        prefs.edit()
            .putInt("community_${safeKey(number)}", count.coerceAtLeast(0))
            .putLong("community_time_${safeKey(number)}", System.currentTimeMillis())
            .apply()
    }

    fun isCommunityCacheFresh(number: String, maxAgeMs: Long = 6 * 60 * 60 * 1000L): Boolean {
        val at = prefs.getLong("community_time_${safeKey(number)}", 0L)
        return at > 0L && System.currentTimeMillis() - at <= maxAgeMs
    }

    fun isBlocked(number: String): Boolean = prefs.getStringSet("blocked_numbers", emptySet())?.contains(number) == true

    fun block(number: String) {
        val set = prefs.getStringSet("blocked_numbers", emptySet())?.toMutableSet() ?: mutableSetOf()
        set += number
        prefs.edit().putStringSet("blocked_numbers", set).apply()
    }

    fun unblock(number: String) {
        val set = prefs.getStringSet("blocked_numbers", emptySet())?.toMutableSet() ?: mutableSetOf()
        set -= number
        prefs.edit().putStringSet("blocked_numbers", set).apply()
    }

    fun addHistory(entry: HistoryEntry) {
        val all = history().toMutableList()
        all.add(0, entry)
        val encoded = all.distinctBy { "${it.kind}|${it.title}|${it.createdAt}" }.take(60).map { encode(it) }.toSet()
        prefs.edit().putStringSet("history", encoded).apply()
    }

    fun history(): List<HistoryEntry> = prefs.getStringSet("history", emptySet()).orEmpty()
        .mapNotNull { decode(it) }
        .sortedByDescending { it.createdAt }

    fun clearHistory() = prefs.edit().remove("history").apply()

    private fun encode(e: HistoryEntry): String = listOf(e.kind, e.title, e.verdict, e.score.toString(), e.createdAt.toString())
        .joinToString("|") { Base64.encodeToString(it.toByteArray(), Base64.NO_WRAP) }

    private fun decode(s: String): HistoryEntry? = runCatching {
        val p = s.split('|').map { String(Base64.decode(it, Base64.NO_WRAP)) }
        HistoryEntry(p[0], p[1], p[2], p[3].toInt(), p[4].toLong())
    }.getOrNull()

    private fun safeKey(s: String): String = Base64.encodeToString(s.toByteArray(), Base64.NO_WRAP or Base64.URL_SAFE)
}
