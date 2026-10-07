package com.pjbuilts.scamlens.services

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import com.pjbuilts.scamlens.MainActivity
import com.pjbuilts.scamlens.R
import com.pjbuilts.scamlens.domain.PhoneRiskResult
import com.pjbuilts.scamlens.domain.ScanResult
import com.pjbuilts.scamlens.domain.Verdict

object ProtectionNotifier {
    const val EXTRA_NUMBER = "extra_number"
    const val ACTION_BLOCK = "com.pjbuilts.scamlens.BLOCK"
    const val ACTION_TRUST = "com.pjbuilts.scamlens.TRUST"
    private const val CALL_CHANNEL = "scamlens_call_guard_v2"
    private const val MESSAGE_CHANNEL = "scamlens_message_guard_v2"

    fun showCallAlert(context: Context, result: PhoneRiskResult, blockedNow: Boolean) {
        ensureChannels(context)
        if (!canNotify(context)) return

        val title = when {
            blockedNow -> "BLOCKED · high-risk caller"
            result.verdict == Verdict.HIGH_RISK -> "HIGH RISK · likely scam call"
            result.verdict == Verdict.SUSPECTED_SCAM -> "SUSPECTED SCAM CALL"
            else -> "UNVERIFIED CALLER · check before trusting"
        }
        val reason = result.reasons.firstOrNull().orEmpty()
        val open = PendingIntent.getActivity(
            context,
            result.normalizedNumber.hashCode(),
            Intent(context, MainActivity::class.java)
                .putExtra(EXTRA_NUMBER, result.displayNumber)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val block = PendingIntent.getBroadcast(
            context,
            result.normalizedNumber.hashCode() + 1,
            Intent(context, ProtectionActionReceiver::class.java)
                .setAction(ACTION_BLOCK)
                .putExtra(EXTRA_NUMBER, result.normalizedNumber),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val trust = PendingIntent.getBroadcast(
            context,
            result.normalizedNumber.hashCode() + 2,
            Intent(context, ProtectionActionReceiver::class.java)
                .setAction(ACTION_TRUST)
                .putExtra(EXTRA_NUMBER, result.normalizedNumber),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val body = result.displayNumber + "\n" + reason + "\n\n" + result.recommendedAction +
            "\n\n" + result.scoreLabel

        val builder = NotificationCompat.Builder(context, CALL_CHANNEL)
            .setSmallIcon(R.drawable.ic_scamlens)
            .setContentTitle(title)
            .setContentText(reason.ifBlank { result.headline })
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setSubText("ScamLens Call Guard")
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_CALL)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setDefaults(NotificationCompat.DEFAULT_ALL)
            .setAutoCancel(true)
            .setContentIntent(open)

        if (!blockedNow && result.normalizedNumber.isNotBlank()) {
            builder.addAction(0, "Block future calls", block)
            builder.addAction(0, "Trust caller", trust)
        }

        NotificationManagerCompat.from(context)
            .notify(41000 + (result.normalizedNumber.hashCode() and 0x0fff), builder.build())
    }

    fun showMessageAlert(context: Context, result: ScanResult, appLabel: String) {
        ensureChannels(context)
        if (!canNotify(context)) return

        val title = when (result.verdict) {
            Verdict.HIGH_RISK -> "HIGH RISK · likely scam message"
            Verdict.SUSPECTED_SCAM -> "SUSPECTED SCAM MESSAGE"
            Verdict.USE_CAUTION -> "CAUTION · suspicious message"
            Verdict.NO_STRONG_SIGNALS -> "ScamLens check"
        }
        val reason = result.signals.firstOrNull()?.detail ?: result.category
        val open = PendingIntent.getActivity(
            context,
            result.rawInput.hashCode(),
            Intent(context, MainActivity::class.java)
                .putExtra("scan_text", result.rawInput)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val body = appLabel + "\n" + result.headline + "\n" + reason +
            "\n\n" + result.actions.firstOrNull().orEmpty() + "\n\n" + result.scoreLabel

        val notification = NotificationCompat.Builder(context, MESSAGE_CHANNEL)
            .setSmallIcon(R.drawable.ic_scamlens)
            .setContentTitle(title)
            .setContentText(result.headline)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setSubText("ScamLens Notification Guard")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_MESSAGE)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setDefaults(NotificationCompat.DEFAULT_ALL)
            .setAutoCancel(true)
            .setContentIntent(open)
            .build()

        NotificationManagerCompat.from(context)
            .notify(52000 + (result.rawInput.hashCode() and 0x0fff), notification)
    }

    private fun canNotify(context: Context): Boolean {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
    }

    private fun ensureChannels(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val nm = context.getSystemService(NotificationManager::class.java)
        nm.createNotificationChannels(
            listOf(
                NotificationChannel(
                    CALL_CHANNEL,
                    "Incoming call protection",
                    NotificationManager.IMPORTANCE_HIGH
                ).apply {
                    description = "Strong ScamLens warnings for suspicious and unverified incoming calls."
                    enableVibration(true)
                    setShowBadge(true)
                },
                NotificationChannel(
                    MESSAGE_CHANNEL,
                    "Message protection",
                    NotificationManager.IMPORTANCE_HIGH
                ).apply {
                    description = "ScamLens warnings for suspicious notification content."
                    enableVibration(true)
                    setShowBadge(true)
                }
            )
        )
    }
}
