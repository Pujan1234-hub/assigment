package com.pjbuilts.scamlens.services

import android.os.Build
import android.telecom.Call
import android.telecom.CallScreeningService
import com.pjbuilts.scamlens.data.LocalStore
import com.pjbuilts.scamlens.domain.PhoneRiskEngine

class ScamCallScreeningService : CallScreeningService() {
    override fun onScreenCall(callDetails: Call.Details) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q &&
            callDetails.callDirection != Call.Details.DIRECTION_INCOMING) {
            respondToCall(callDetails, CallResponse.Builder().build())
            return
        }

        val rawNumber = callDetails.handle?.schemeSpecificPart
        val normalized = PhoneRiskEngine.normalize(rawNumber)
        val store = LocalStore(this)
        val repeats = store.recordCallAndCountRecent(normalized)
        val result = PhoneRiskEngine.analyse(
            rawNumber = rawNumber,
            locallyReported = store.isReported(normalized),
            locallyBlocked = store.isBlocked(normalized),
            locallyAllowed = store.isAllowed(normalized),
            repeatCallsInTenMinutes = repeats,
            autoBlockHighRisk = store.autoBlockHighRisk
        )

        val blockNow = store.isBlocked(normalized) || result.shouldAutoBlock
        val response = CallResponse.Builder()
            .setDisallowCall(blockNow)
            .setRejectCall(blockNow)
            .setSkipCallLog(false)
            .setSkipNotification(false)
            .build()

        respondToCall(callDetails, response)
        store.addCall(result, blockNow)

        // Default to quiet for ordinary unknown callers. An explicit opt-in still
        // allows neutral identification notices without branding them scammers.
        if (store.warnEveryUnverifiedCall ||
            result.verdict == com.pjbuilts.scamlens.domain.Verdict.SUSPECTED_SCAM ||
            result.verdict == com.pjbuilts.scamlens.domain.Verdict.HIGH_RISK ||
            result.verdict == com.pjbuilts.scamlens.domain.Verdict.USE_CAUTION ||
            blockNow
        ) {
            ProtectionNotifier.showCallAlert(this, result, blockNow)
        }
    }
}
