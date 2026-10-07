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

        if (locallyAllowed) {
            return PhoneRiskResult(
                displayNumber = display,
                normalizedNumber = normalized,
                score = 0,
                verdict = Verdict.NO_STRONG_SIGNALS,
                reasons = listOf("You marked this caller as trusted on this device."),
                recommendedAction = "Trusted locally. Stay alert if the caller asks for money, passwords, OTPs or remote access."
            )
        }

        if (locallyBlocked) {
            return PhoneRiskResult(
                displayNumber = display,
                normalizedNumber = normalized,
                score = 100,
                verdict = Verdict.HIGH_RISK,
                reasons = listOf("This number is on your ScamLens block list."),
                recommendedAction = "Keep the call blocked. Only unblock it after independent verification.",
                shouldAutoBlock = true
            )
        }

        var score = if (normalized.isBlank()) 0 else 5

        if (normalized.isBlank()) {
            score += 58
            reasons += "Caller ID is hidden or unavailable, so the caller cannot be independently verified."
        } else {
            reasons += "This caller is not on your trusted list. Caller ID alone does not prove who is calling."
        }

        if (locallyReported) {
            score += 70
            reasons += "You previously reported this number as suspicious on this device."
        }

        when {
            repeatCallsInTenMinutes >= 4 -> {
                score += 42
                reasons += "Four or more calls from this number were detected within ten minutes."
            }
            repeatCallsInTenMinutes == 3 -> {
                score += 30
                reasons += "Three calls from this number were detected within ten minutes."
            }
            repeatCallsInTenMinutes == 2 -> {
                score += 16
                reasons += "This number called more than once within ten minutes."
            }
        }

        if (normalized.isNotBlank() && !isPlausible(normalized)) {
            score += 32
            reasons += "The caller ID format looks incomplete or implausible."
        }

        if (normalized.isNotBlank() && isHigherCostUkRange(normalized)) {
            score += 12
            reasons += "This looks like a UK higher-cost or personal-numbering range. That is not proof of a scam, but unexpected calls deserve extra caution."
        }

        score = score.coerceIn(0, 100)
        val verdict = when {
            score >= 85 -> Verdict.HIGH_RISK
            score >= 52 -> Verdict.SUSPECTED_SCAM
            score >= 25 -> Verdict.USE_CAUTION
            normalized.isNotBlank() -> Verdict.USE_CAUTION
            else -> Verdict.SUSPECTED_SCAM
        }

        val action = when (verdict) {
            Verdict.HIGH_RISK -> "End or block the call. Do not send money, share passwords or OTPs, or allow remote access."
            Verdict.SUSPECTED_SCAM -> "Do not trust the caller's story or caller ID. End the call and contact the organisation using a number you already know."
            Verdict.USE_CAUTION -> "Caller is unverified. Avoid sensitive information and verify independently before acting."
            Verdict.NO_STRONG_SIGNALS -> "Trusted locally, but remain cautious if the conversation becomes unusual."
        }

        return PhoneRiskResult(
            displayNumber = display,
            normalizedNumber = normalized,
            score = score,
            verdict = verdict,
            reasons = reasons.distinct(),
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

    private fun isHigherCostUkRange(number: String): Boolean {
        val compact = number.removePrefix("+44").removePrefix("0044").removePrefix("0")
        return compact.startsWith("9") || compact.startsWith("70")
    }
}
