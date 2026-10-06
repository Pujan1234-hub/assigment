package com.pjbuilts.scamlens.domain

object PhoneRiskEngine {
    fun analyse(
        rawNumber: String?,
        locallyReported: Boolean = false,
        locallyBlocked: Boolean = false,
        locallyAllowed: Boolean = false,
        repeatCallsInTenMinutes: Int = 0,
        autoBlockHighRisk: Boolean = false
    ): PhoneRiskResult {
        val display = rawNumber?.trim().orEmpty().ifBlank { "Private / withheld number" }
        val normalized = normalize(rawNumber)
        val reasons = mutableListOf<String>()
        var score = 0

        if (locallyAllowed) {
            return PhoneRiskResult(
                display, normalized, 0, Verdict.NO_STRONG_SIGNALS,
                listOf("You marked this caller as trusted on this device."),
                "Trusted locally. Stay alert if the conversation becomes unusual."
            )
        }

        if (rawNumber.isNullOrBlank() || normalized.isBlank()) {
            score += 55
            reasons += "Caller ID is hidden or unavailable, so the caller cannot be independently verified."
        } else {
            reasons += "This caller is not on your local trusted list."
        }
        if (locallyReported) {
            score += 55
            reasons += "You previously reported this number as suspicious on this device."
        }
        if (locallyBlocked) {
            score = 100
            reasons += "This number is on your local ScamLens block list."
        }
        if (repeatCallsInTenMinutes >= 3) {
            score += 30
            reasons += "Repeated calls from the same number were detected in a short period."
        } else if (repeatCallsInTenMinutes == 2) {
            score += 15
            reasons += "This number called more than once in a short period."
        }
        if (normalized.isNotBlank() && !isPlausible(normalized)) {
            score += 18
            reasons += "The caller ID format looks unusual or incomplete."
        }

        score = score.coerceIn(0, 100)
        val verdict = when {
            score >= 75 -> Verdict.HIGH_RISK
            score >= 50 -> Verdict.SUSPECTED_SCAM
            score >= 25 -> Verdict.USE_CAUTION
            normalized.isNotBlank() -> Verdict.USE_CAUTION
            else -> Verdict.NO_STRONG_SIGNALS
        }
        val action = when (verdict) {
            Verdict.HIGH_RISK -> "Do not share money, passwords, OTPs or remote-access control. End the call and verify independently."
            Verdict.SUSPECTED_SCAM -> "Use caution. Do not trust caller ID alone; verify the organisation using a known official number."
            Verdict.USE_CAUTION -> "Caller is unverified. Avoid sensitive information and verify independently."
            Verdict.NO_STRONG_SIGNALS -> "No strong local signal found. This does not prove the caller is safe."
        }

        return PhoneRiskResult(
            displayNumber = display,
            normalizedNumber = normalized,
            score = score,
            verdict = verdict,
            reasons = reasons,
            recommendedAction = action,
            shouldAutoBlock = autoBlockHighRisk && score >= 85
        )
    }

    fun normalize(raw: String?): String =
        raw.orEmpty().trim().replace(Regex("[^+0-9]"), "")

    private fun isPlausible(number: String): Boolean {
        val digits = number.count { it.isDigit() }
        if (digits in 3..6) return true
        return digits in 7..15
    }
}
