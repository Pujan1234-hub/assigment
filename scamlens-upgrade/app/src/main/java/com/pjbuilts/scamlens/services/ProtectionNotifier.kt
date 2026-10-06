package com.pjbuilts.scamlens.services

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.pjbuilts.scamlens.MainActivity
import com.pjbuilts.scamlens.R
import com.pjbuilts.scamlens.domain.PhoneRiskResult
import com.pjbuilts.scamlens.domain.ScanResult
import com.pjbuilts.scamlens.domain.Verdict

object ProtectionNotifier {
    const val EXTRA_NUMBER = "extra_number"
    const val ACTION_BLOCK = "com.pjbuilts.scamlens.BLOCK"
    const val ACTION_TRUST = "com.pjbuilts.scamlens.TRUST"
    private const val CALL_CHANNEL = "scamlens_call_guard"
    private const val MESSAGE_CHANNEL = "scamlens_message_guard"

    fun showCallAlert(context: Context, result: PhoneRiskResult, blockedNow: Boolean) {
        ensureChannels(context)
        val title = when {
            blockedNow -> "ScamLens blocked a high-risk call"
            result.verdict == Verdict.HIGH_RISK -> "High-risk caller detected"
            result.verdict == Verdict.SUSPECTED_SCAM -> "Suspected scam call"
            else -> "UNVERIFIED CALLER · use caution"
        }
        val reason = result.reasons.firstOrNull().orEmpty()
        val open = PendingIntent.getActivity(
            context, result.normalizedNumber.hashCode(),
            Intent(context, MainActivity::class.java)
                .putExtra(EXTRA_NUMBER, result.displayNumber)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val block = PendingIntent.getBroadcast(
            context, result.normalizedNumber.hashCode() + 1,
            Intent(context, ProtectionActionReceiver::class.java)
                .setAction(ACTION_BLOCK).putExtra(EXTRA_NUMBER, result.normalizedNumber),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val trust = PendingIntent.getBroadcast(
            context, result.normalizedNumber.hashCode() + 2,
            Intent(context, ProtectionActionReceiver::class.java)
                .setAction(ACTION_TRUST).putExtra(EXTRA_NUMBER, result.normalizedNumber),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val b = NotificationCompat.Builder(context, CALL_CHANNEL)
            .setSmallIcon(R.drawable.ic_scamlens)
            .setContentTitle(title)
            .setContentText(result.displayNumber + " · " + result.score + "/100 evidence risk")
            .setStyle(NotificationCompat.BigTextStyle().bigText(
                result.displayNumber + " · " + result.score + "/100 evidence risk\n" + reason + "\n\n" + result.recommendedAction
            ))
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_CALL)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setAutoCancel(true)
            .setContentIntent(open)

        if (!blockedNow && result.normalizedNumber.isNotBlank()) {
            b.addAction(0, "Block future calls", block)
            b.addAction(0, "Trust caller", trust)
        }
        try {
            NotificationManagerCompat.from(context).notify(41000 + (result.normalizedNumber.hashCode() and 0x0fff), b.build())
        } catch (_: SecurityException) {}
    }

    fun showMessageAlert(context: Context, result: ScanResult, appLabel: String) {
        ensureChannels(context)
        val title = when (result.verdict) {
            Verdict.HIGH_RISK -> "High-risk message detected"
            Verdict.SUSPECTED_SCAM -> "Suspected scam message"
            Verdict.USE_CAUTION -> "Suspicious message · check first"
            Verdict.NO_STRONG_SIGNALS -> "ScamLens check"
        }
        val reason = result.signals.firstOrNull()?.detail ?: result.category
        val open = PendingIntent.getActivity(
            context, result.rawInput.hashCode(),
            Intent(context, MainActivity::class.java)
                .putExtra("scan_text", result.rawInput)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val n = NotificationCompat.Builder(context, MESSAGE_CHANNEL)
            .setSmallIcon(R.drawable.ic_scamlens)
            .setContentTitle(title)
            .setContentText(appLabel + " · " + result.score + "/100")
            .setStyle(NotificationCompat.BigTextStyle().bigText(
                appLabel + " · " + result.score + "/100\n" + reason + "\n\nOpen ScamLens to review the evidence before acting."
            ))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(open)
            .build()
        try {
            NotificationManagerCompat.from(context).notify(52000 + (result.rawInput.hashCode() and 0x0fff), n)
        } catch (_: SecurityException) {}
    }

    private fun ensureChannels(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val nm = context.getSystemService(NotificationManager::class.java)
        nm.createNotificationChannels(listOf(
            NotificationChannel(CALL_CHANNEL, "Incoming call protection", NotificationManager.IMPORTANCE_HIGH).apply {
                description = "ScamLens warnings for suspicious and unverified incoming calls."
                enableVibration(true)
            },
            NotificationChannel(MESSAGE_CHANNEL, "Message protection", NotificationManager.IMPORTANCE_HIGH).apply {
                description = "ScamLens warnings for suspicious incoming notification content."
                enableVibration(true)
            }
        ))
    }
}
