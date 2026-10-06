package com.pjbuilts.scamlens.services

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import com.pjbuilts.scamlens.domain.LiveThreatClient
import com.pjbuilts.scamlens.domain.PrivacyRedactor
import com.pjbuilts.scamlens.domain.ProtectionStore
import com.pjbuilts.scamlens.domain.RiskEngine
import com.pjbuilts.scamlens.domain.RiskLevel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class ScamNotificationListenerService : NotificationListenerService() {
    private val seen = LinkedHashMap<String, Long>()
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        sbn ?: return
        if (sbn.packageName == packageName) return
        val extras = sbn.notification.extras
        val title = extras.getCharSequence("android.title")?.toString().orEmpty()
        val text = extras.getCharSequence("android.text")?.toString().orEmpty()
        val big = extras.getCharSequence("android.bigText")?.toString().orEmpty()
        val combined = listOf(title, text, big).filter { it.isNotBlank() }.distinct().joinToString("\n")
        if (combined.length < 12) return

        val key = "${sbn.packageName}:${combined.hashCode()}"
        val now = System.currentTimeMillis()
        seen.entries.removeIf { now - it.value > 30 * 60_000L }
        if (seen.containsKey(key)) return
        seen[key] = now

        val store = ProtectionStore(this)
        val local = RiskEngine.analyse(combined)
        if (local.level >= RiskLevel.HIGH) notifyResult(store, local, combined, key)

        val url = RiskEngine.extractUrls(combined).firstOrNull() ?: return
        if (!store.liveUrlChecks && !store.communityIntel) return

        scope.launch {
            var enriched = local
            if (store.liveUrlChecks) {
                val phish = LiveThreatClient.phishTankLookup(url)
                enriched = RiskEngine.augmentWithPhishingIntel(enriched, phish, "PhishTank")
            }
            if (store.communityIntel) {
                val host = RiskEngine.hostOf(url)
                if (host.isNotBlank()) {
                    val reports = LiveThreatClient.communityLookup("domain", host)
                    enriched = RiskEngine.augmentWithCommunityReports(enriched, reports, host)
                }
            }
            if (enriched.level >= RiskLevel.MEDIUM && enriched.score > local.score) {
                notifyResult(store, enriched, combined, "$key-live")
            }
        }
    }

    private fun notifyResult(store: ProtectionStore, result: com.pjbuilts.scamlens.domain.ScanResult, combined: String, key: String) {
        val preview = if (store.privacyRedaction) PrivacyRedactor.redact(combined) else combined
        ScamNotificationHelper.forResult(this, result, "Suspicious notification detected", key.hashCode(), preview)
    }
}
