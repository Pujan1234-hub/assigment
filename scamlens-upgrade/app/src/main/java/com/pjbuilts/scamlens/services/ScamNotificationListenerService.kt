package com.pjbuilts.scamlens.services

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import com.pjbuilts.scamlens.data.LocalStore
import com.pjbuilts.scamlens.domain.RiskEngine
import com.pjbuilts.scamlens.domain.ScanSource
import com.pjbuilts.scamlens.domain.Verdict

class ScamNotificationListenerService : NotificationListenerService() {
    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        if (sbn == null || sbn.packageName == packageName) return

        val store = LocalStore(this)
        if (!store.notificationGuardEnabled) return

        val notification = sbn.notification ?: return
        if ((notification.flags and Notification.FLAG_ONGOING_EVENT) != 0) return
        if ((notification.flags and Notification.FLAG_GROUP_SUMMARY) != 0) return

        val extras = notification.extras ?: return
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString().orEmpty()
        val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString().orEmpty()
        val big = extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString().orEmpty()
        val sub = extras.getCharSequence(Notification.EXTRA_SUB_TEXT)?.toString().orEmpty()
        val lines = extras.getCharSequenceArray(Notification.EXTRA_TEXT_LINES)
            ?.map { it.toString() }
            .orEmpty()

        val combined = (listOf(title, text, big, sub) + lines)
            .filter { it.isNotBlank() }
            .distinct()
            .joinToString("\n")
            .trim()

        if (combined.length < 12) return

        val result = RiskEngine.analyse(combined, ScanSource.NOTIFICATION)
        val meaningful = result.score >= 26
        val urgent = result.verdict == Verdict.SUSPECTED_SCAM ||
            result.verdict == Verdict.HIGH_RISK ||
            (result.verdict == Verdict.USE_CAUTION && result.signals.any { it.points >= 24 })

        if (meaningful) store.addScan(result)
        if (!urgent) return

        val fingerprint = sbn.packageName + "|" + combined.take(240)
        if (!store.shouldAlert(fingerprint)) return

        val appLabel = try {
            packageManager.getApplicationLabel(
                packageManager.getApplicationInfo(sbn.packageName, 0)
            ).toString()
        } catch (_: Exception) {
            sbn.packageName
        }

        ProtectionNotifier.showMessageAlert(this, result, appLabel)
    }
}
