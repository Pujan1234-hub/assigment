package com.pjbuilts.scamlens.domain

import android.content.Context
import android.provider.Settings
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.security.MessageDigest

object LiveThreatClient {
    private const val SCAMLENS_INTEL = "https://nvfqxsnyrgjszrvmlrgf.supabase.co/functions/v1/scamlens-intel"

    suspend fun phishTankLookup(url: String): Boolean = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
        runCatching {
            val body = "url=${URLEncoder.encode(url, "UTF-8")}&format=xml"
            val conn = (URL("https://checkurl.phishtank.com/checkurl/").openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 2500
                readTimeout = 2500
                doOutput = true
                setRequestProperty("Content-Type", "application/x-www-form-urlencoded")
                setRequestProperty("User-Agent", "ScamLens-PJBUILTS-Android/0.9")
            }
            conn.outputStream.use { it.write(body.toByteArray()) }
            val text = (if (conn.responseCode in 200..299) conn.inputStream else conn.errorStream)
                ?.bufferedReader()?.use { it.readText() }.orEmpty()
            conn.disconnect()
            val inDb = text.contains("<in_database>true</in_database>", true) || text.contains("<in_database>y</in_database>", true)
            val verified = text.contains("<verified>true</verified>", true) || text.contains("<verified>y</verified>", true)
            val valid = text.contains("<valid>true</valid>", true) || text.contains("<valid>y</valid>", true)
            inDb && (verified || valid)
        }.getOrDefault(false)
    }

    suspend fun communityLookup(type: String, indicator: String): Int = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
        postJson(JSONObject().apply {
            put("action", "lookup")
            put("type", type)
            put("indicator", indicator.lowercase())
        })?.optInt("report_count", 0) ?: 0
    }

    suspend fun communityReport(context: Context, type: String, indicator: String, category: String = "scam"): Int =
        kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
            postJson(JSONObject().apply {
                put("action", "report")
                put("type", type)
                put("indicator", indicator.lowercase())
                put("reporter_hash", reporterHash(context))
                put("category", category.take(64))
            })?.optInt("report_count", 0) ?: 0
        }

    private fun postJson(payload: JSONObject): JSONObject? = runCatching {
        val conn = (URL(SCAMLENS_INTEL).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 1800
            readTimeout = 1800
            doOutput = true
            setRequestProperty("Content-Type", "application/json")
            setRequestProperty("Accept", "application/json")
            setRequestProperty("User-Agent", "ScamLens-PJBUILTS-Android/0.9")
        }
        conn.outputStream.use { it.write(payload.toString().toByteArray()) }
        val text = (if (conn.responseCode in 200..299) conn.inputStream else conn.errorStream)
            ?.bufferedReader()?.use { it.readText() }.orEmpty()
        val code = conn.responseCode
        conn.disconnect()
        if (code !in 200..299 || text.isBlank()) null else JSONObject(text)
    }.getOrNull()

    private fun reporterHash(context: Context): String {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID).orEmpty()
        val raw = "scamlens:${context.packageName}:$androidId"
        return MessageDigest.getInstance("SHA-256").digest(raw.toByteArray()).joinToString("") { "%02x".format(it) }
    }
}
