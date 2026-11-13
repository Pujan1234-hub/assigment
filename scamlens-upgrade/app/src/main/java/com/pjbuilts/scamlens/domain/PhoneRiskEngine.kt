package com.pjbuilts.scamlens.domain

/**
 * Local evidence only. Missing caller ID, missing contacts and unknown numbers
 * are not evidence of fraud. Do not invent reverse-lookup identities.
 */
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
        if (locallyAllowed) {
            return PhoneRiskResult(
                display, normalized, 0, Verdict.NO_STRONG_SIGNALS,
                listOf("You marked this caller as trusted on this device."),
                "Your local trust decision is not identity verification. Never share OTPs, passwords or bank details.",
                trustedLocally = true
            )
        }
        if (locallyBlocked) {
            return PhoneRiskResult(
                display, normalized, 0, Verdict.NO_STRONG_SIGNALS,
                listOf("You blocked this number on this device; that does not independently prove fraud."),
                "Blocked by your own choice. You can remove the block after independent verification.",
                shouldAutoBlock = true,
                blockedLocally = true
            )
        }

        val reasons = mutableListOf<String>()
        var score = 0
        if (normalized.isBlank()) {
            reasons += "Caller ID is withheld. A private number is not proof of fraud."
        } else {
            reasons += "Caller identity is unknown. Being absent from contacts is not a scam signal."
        }
        if (locallyReported) {
            score += 65
            reasons += "You previously reported this number on this device. This is a personal report, not a verified community finding."
        }
        when {
            repeatCallsInTenMinutes >= 4 -> {
                score += 20
                reasons += "Four or more calls were observed within ten minutes. Repeated calls can also come from genuine recruiters."
            }
            repeatCallsInTenMinutes == 3 -> {
                score += 10
                reasons += "Three calls were observed within ten minutes."
            }
            repeatCallsInTenMinutes == 2 -> {
                score += 4
                reasons += "This number called twice within ten minutes."
            }
        }
        if (normalized.isNotBlank() && !isPlausible(normalized)) {
            score += 12
            reasons += "The caller ID format appears incomplete or unusual; it may still have a legitimate explanation."
        }
        if (normalized.isNotBlank() && isHigherCostUkRange(normalized)) {
            score += 8
            reasons += "This may be a higher-cost UK numbering range; check charges before calling back."
        }
        score = score.coerceIn(0, 100)

        val verdict = when {
            locallyReported && score >= 85 -> Verdict.HIGH_RISK
            locallyReported -> Verdict.SUSPECTED_SCAM
            score >= 25 -> Verdict.USE_CAUTION
            else -> Verdict.NO_STRONG_SIGNALS
        }
        val action = when (verdict) {
            Verdict.HIGH_RISK -> "Repeated calls from a number you reported. Verify through a trusted number and review your report before blocking."
            Verdict.SUSPECTED_SCAM -> "You reported this caller before. Verify independently; a personal report is not definitive proof."
            Verdict.USE_CAUTION -> "Some unusual calling behaviour was observed. Verify the caller before sharing sensitive information."
            Verdict.NO_STRONG_SIGNALS -> "No local scam evidence found. Unknown does not mean safe or fraudulent; verify requests for money or security codes."
        }
        return PhoneRiskResult(
            displayNumber = display,
            normalizedNumber = normalized,
            score = score,
            verdict = verdict,
            reasons = reasons.distinct(),
            recommendedAction = action,
            shouldAutoBlock = autoBlockHighRisk && locallyReported && repeatCallsInTenMinutes >= 4 && score >= 85,
            reportedLocally = locallyReported
        )
    }

    fun normalize(raw: String?): String =
        raw.orEmpty().trim().replace(Regex("[^+0-9]"), "")

    private fun isPlausible(number: String): Boolean {
        val digits = number.count { it.isDigit() }
        return digits in 3..15
    }

    private fun isHigherCostUkRange(number: String): Boolean {
        val compact = number.removePrefix("+44").removePrefix("0044").removePrefix("0")
        return compact.startsWith("9") || compact.startsWith("70")
    }
}
