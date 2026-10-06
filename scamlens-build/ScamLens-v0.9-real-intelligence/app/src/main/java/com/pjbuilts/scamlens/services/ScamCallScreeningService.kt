package com.pjbuilts.scamlens.services

import android.telecom.Call
import android.telecom.CallScreeningService
import com.pjbuilts.scamlens.domain.LiveThreatClient
import com.pjbuilts.scamlens.domain.PhoneRiskEngine
import com.pjbuilts.scamlens.domain.ProtectionStore
import com.pjbuilts.scamlens.domain.RiskLevel
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeoutOrNull

class ScamCallScreeningService : CallScreeningService() {
    override fun onScreenCall(callDetails: Call.Details) {
        val number = callDetails.handle?.schemeSpecificPart
        val clean = PhoneRiskEngine.normalize(number)
        val store = ProtectionStore(this)

        val communityCount = if (store.communityIntel && clean.length >= 7) {
            val cached = store.communityReportCount(clean)
            if (store.isCommunityCacheFresh(clean)) cached else {
                runBlocking {
                    withTimeoutOrNull(1700L) {
                        LiveThreatClient.communityLookup("phone", clean).also { store.cacheCommunityReportCount(clean, it) }
                    }
                } ?: cached
            }
        } else store.communityReportCount(clean)

        val result = PhoneRiskEngine.analyse(this, number, communityCount)
        val shouldBlock = store.autoBlockHighRisk && result.level >= RiskLevel.HIGH
        val shouldSilence = !shouldBlock && store.silenceHighRisk && result.level >= RiskLevel.HIGH

        respondToCall(
            callDetails,
            CallResponse.Builder()
                .setDisallowCall(shouldBlock)
                .setRejectCall(shouldBlock)
                .setSilenceCall(shouldSilence)
                .setSkipCallLog(false)
                .setSkipNotification(shouldBlock)
                .build()
        )

        // Always show a caller verdict while Call Protection is active. This makes screening visible
        // even for a brand-new number with no reputation history; we never label that as "safe".
        val why = result.signals.take(2).joinToString(" • ") { it.title }.ifBlank { "No reputation history yet" }
        val title = when {
            shouldBlock -> "ScamLens blocked a high-risk caller"
            shouldSilence -> "ScamLens silenced a high-risk caller"
            result.level >= RiskLevel.HIGH -> "ScamLens: HIGH-RISK CALLER"
            result.level == RiskLevel.MEDIUM -> "ScamLens: suspicious caller"
            else -> "ScamLens: caller unverified"
        }
        ScamNotificationHelper.notify(
            this,
            title,
            "${number ?: "Unknown caller"}: ${result.verdict}. $why",
            (number ?: "unknown").hashCode(),
            phone = number
        )

        store.addHistory(
            com.pjbuilts.scamlens.domain.HistoryEntry(
                "Caller",
                number ?: "Unknown caller",
                result.verdict,
                result.score,
                System.currentTimeMillis()
            )
        )
    }
}
