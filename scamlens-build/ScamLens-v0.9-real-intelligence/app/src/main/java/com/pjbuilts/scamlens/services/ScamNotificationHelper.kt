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
import com.pjbuilts.scamlens.domain.ScanResult

object ScamNotificationHelper {
    private const val CHANNEL = "scamlens_protection_alerts"

    fun notify(context: Context, title: String, body: String, id: Int, extraText: String? = null, phone: String? = null) {
        createChannel(context)
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            extraText?.let { putExtra("scan_text", it) }
            phone?.let { putExtra("phone_number", it) }
        }
        val pending = PendingIntent.getActivity(context, id, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val notification = NotificationCompat.Builder(context, CHANNEL)
            .setSmallIcon(R.drawable.ic_scamlens_logo)
            .setContentTitle(title)
            .setContentText(body)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setAutoCancel(true)
            .setContentIntent(pending)
            .build()
        runCatching { NotificationManagerCompat.from(context).notify(id, notification) }
    }

    fun forResult(context: Context, result: ScanResult, source: String, id: Int, extraText: String? = null) {
        val title = when (result.level) {
            com.pjbuilts.scamlens.domain.RiskLevel.CRITICAL -> "ScamLens: likely scam"
            com.pjbuilts.scamlens.domain.RiskLevel.HIGH -> "ScamLens: high-risk warning"
            com.pjbuilts.scamlens.domain.RiskLevel.MEDIUM -> "ScamLens: caution"
            else -> return
        }
        val why = result.signals.take(2).joinToString(" • ") { it.title }
        notify(context, title, "$source: ${result.verdict}. $why", id, extraText)
    }

    private fun createChannel(context: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val nm = context.getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(NotificationChannel(CHANNEL, "Scam protection alerts", NotificationManager.IMPORTANCE_HIGH).apply {
                description = "Warnings for suspicious calls and message notifications"
            })
        }
    }
}
