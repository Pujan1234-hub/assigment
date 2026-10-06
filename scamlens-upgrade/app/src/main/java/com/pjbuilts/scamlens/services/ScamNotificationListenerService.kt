package com.pjbuilts.scamlens.services

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import com.pjbuilts.scamlens.data.LocalStore
import com.pjbuilts.scamlens.domain.RiskEngine
import com.pjbuilts.scamlens.domain.ScanSource

class ScamNotificationListenerService : NotificationListenerService() {
    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        if (sbn == null || sbn.packageName == packageName) return
        val store = LocalStore(this)
        if (!store.notificationGuardEnabled) return

        val notification = sbn.notification ?: return
        if ((notification.flags and Notification.FLAG_ONGOING_EVENT) != 0) return

        val extras = notification.extras ?: return
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString().orEmpty()
        val text = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString().orEmpty()
        val big = extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString().orEmpty()
        val combined = listOf(title, text, big)
            .filter { it.isNotBlank() }
            .distinct()
            .joinToString("\n")
            .trim()
        if (combined.length < 12) return

        val result = RiskEngine.analyse(combined, ScanSource.NOTIFICATION)
        // Only persist/warn when there is a meaningful signal. This avoids building a shadow inbox.
        if (result.score >= 25) store.addScan(result)
        if (result.score >= 45) {
            val appLabel = try {
                packageManager.getApplicationLabel(packageManager.getApplicationInfo(sbn.packageName, 0)).toString()
            } catch (_: Exception) {
                sbn.packageName
            }
            ProtectionNotifier.showMessageAlert(this, result, appLabel)
        }
    }
}
