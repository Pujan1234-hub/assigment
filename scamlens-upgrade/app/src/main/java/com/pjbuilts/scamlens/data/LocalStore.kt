package com.pjbuilts.scamlens.data

import android.content.Context
import com.pjbuilts.scamlens.domain.PhoneRiskResult
import com.pjbuilts.scamlens.domain.ScanResult
import org.json.JSONArray
import org.json.JSONObject
import java.security.MessageDigest

class LocalStore(context: Context) {
    private val prefs = context.getSharedPreferences("scamlens_local", Context.MODE_PRIVATE)

    var autoBlockHighRisk: Boolean
        get() = prefs.getBoolean("auto_block_high", false)
        set(value) = prefs.edit().putBoolean("auto_block_high", value).apply()

    var warnEveryUnverifiedCall: Boolean
        get() = prefs.getBoolean("warn_unverified_calls", true)
        set(value) = prefs.edit().putBoolean("warn_unverified_calls", value).apply()

    var notificationGuardEnabled: Boolean
        get() = prefs.getBoolean("notification_guard_enabled", true)
        set(value) = prefs.edit().putBoolean("notification_guard_enabled", value).apply()

    fun addScan(result: ScanResult) {
        val item = JSONObject()
            .put("kind", result.source.name)
            .put("score", result.score)
            .put("verdict", result.verdictLabel)
            .put("category", result.category)
            .put("preview", redact(result.rawInput))
            .put("time", System.currentTimeMillis())
        appendHistory(item)
    }

    fun addCall(result: PhoneRiskResult, blocked: Boolean) {
        val item = JSONObject()
            .put("kind", "CALL")
            .put("score", result.score)
            .put("verdict", result.verdictLabel)
            .put("category", if (blocked) "Blocked incoming call" else "Incoming call")
            .put("preview", maskNumber(result.displayNumber))
            .put("time", System.currentTimeMillis())
        appendHistory(item)
    }

    fun getHistory(limit: Int = 60): List<HistoryItem> {
        val arr = readArray("history")
        return buildList {
            for (i in 0 until minOf(arr.length(), limit)) {
                val o = arr.optJSONObject(i) ?: continue
                add(
                    HistoryItem(
                        kind = o.optString("kind"),
                        score = o.optInt("score"),
                        verdict = o.optString("verdict"),
                        category = o.optString("category"),
                        preview = o.optString("preview"),
                        time = o.optLong("time")
                    )
                )
            }
        }
    }

    fun clearHistory() = prefs.edit().remove("history").apply()

    fun reportNumber(number: String) = addToSet("reported_numbers", number)
    fun blockNumber(number: String) = addToSet("blocked_numbers", number)
    fun allowNumber(number: String) {
        addToSet("allowed_numbers", number)
        removeFromSet("blocked_numbers", number)
        removeFromSet("reported_numbers", number)
    }

    fun isReported(number: String): Boolean = normalizedSet("reported_numbers").contains(number)
    fun isBlocked(number: String): Boolean = normalizedSet("blocked_numbers").contains(number)
    fun isAllowed(number: String): Boolean = normalizedSet("allowed_numbers").contains(number)

    fun recordCallAndCountRecent(number: String): Int {
        if (number.isBlank()) return 0
        val key = "call_times_${hash(number)}"
        val now = System.currentTimeMillis()
        val cutoff = now - 10 * 60 * 1000L
        val old = prefs.getString(key, "").orEmpty()
            .split(',')
            .mapNotNull { it.toLongOrNull() }
            .filter { it >= cutoff }
        val updated = (old + now).takeLast(8)
        prefs.edit().putString(key, updated.joinToString(",")).apply()
        return updated.size
    }

    private fun appendHistory(item: JSONObject) {
        val current = readArray("history")
        val next = JSONArray().put(item)
        for (i in 0 until minOf(current.length(), 59)) next.put(current.opt(i))
        prefs.edit().putString("history", next.toString()).apply()
    }

    private fun readArray(key: String): JSONArray = try {
        JSONArray(prefs.getString(key, "[]") ?: "[]")
    } catch (_: Exception) {
        JSONArray()
    }

    private fun normalizedSet(key: String): Set<String> =
        prefs.getStringSet(key, emptySet()).orEmpty().filter { it.isNotBlank() }.toSet()

    private fun addToSet(key: String, number: String) {
        if (number.isBlank()) return
        val copy = normalizedSet(key).toMutableSet().apply { add(number) }
        prefs.edit().putStringSet(key, copy).apply()
    }

    private fun removeFromSet(key: String, number: String) {
        val copy = normalizedSet(key).toMutableSet().apply { remove(number) }
        prefs.edit().putStringSet(key, copy).apply()
    }

    private fun redact(value: String): String {
        val compact = value.replace(Regex("\\s+"), " ").trim().take(120)
        return compact
            .replace(Regex("(?i)\\b\\d{6}\\b"), "••••••")
            .replace(Regex("(?i)(password|passcode|pin)\\s*[:=]?\\s*\\S+")) { match -> "${match.groupValues[1]}: ••••" }
    }

    private fun maskNumber(value: String): String {
        val digits = value.filter { it.isDigit() }
        if (digits.length < 5) return value
        return "•••• ${digits.takeLast(4)}"
    }

    private fun hash(value: String): String {
        val bytes = MessageDigest.getInstance("SHA-256").digest(value.toByteArray())
        return bytes.take(8).joinToString("") { "%02x".format(it) }
    }
}

data class HistoryItem(
    val kind: String,
    val score: Int,
    val verdict: String,
    val category: String,
    val preview: String,
    val time: Long
)
