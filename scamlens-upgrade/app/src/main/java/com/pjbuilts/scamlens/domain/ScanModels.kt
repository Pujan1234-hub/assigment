package com.pjbuilts.scamlens.domain

enum class RiskLevel { LOW, MEDIUM, HIGH, CRITICAL }
enum class Verdict { NO_STRONG_SIGNALS, USE_CAUTION, SUSPECTED_SCAM, HIGH_RISK }
enum class ScanSource { MANUAL, SHARED, SCREENSHOT, QR, NOTIFICATION, PHONE, CALL }

data class RiskSignal(
    val title: String,
    val detail: String,
    val points: Int
) {
    val strengthLabel: String
        get() = when {
            points >= 30 -> "strong"
            points >= 18 -> "meaningful"
            else -> "supporting"
        }
}

data class ScanResult(
    val rawInput: String,
    val score: Int,
    val level: RiskLevel,
    val verdict: Verdict,
    val category: String,
    val signals: List<RiskSignal>,
    val actions: List<String>,
    val source: ScanSource = ScanSource.MANUAL
) {
    val verdictLabel: String
        get() = when (verdict) {
            Verdict.NO_STRONG_SIGNALS -> "No strong scam signals"
            Verdict.USE_CAUTION -> "Unverified · use caution"
            Verdict.SUSPECTED_SCAM -> "Suspected scam"
            Verdict.HIGH_RISK -> "High risk · likely scam"
        }

    val headline: String
        get() = when (verdict) {
            Verdict.NO_STRONG_SIGNALS -> "Nothing strongly suspicious was found"
            Verdict.USE_CAUTION -> "Check this before you trust it"
            Verdict.SUSPECTED_SCAM -> "This matches multiple scam patterns"
            Verdict.HIGH_RISK -> "Stop — strong scam evidence detected"
        }

    val evidenceSummary: String
        get() = when {
            signals.isEmpty() -> "ScamLens found no strong local evidence. That is not a guarantee that the content is safe."
            signals.size == 1 -> "ScamLens found 1 evidence signal: " + signals.first().title + "."
            else -> "ScamLens found " + signals.size + " evidence signals. Strongest: " + signals.first().title + "."
        }

    val scoreLabel: String
        get() = "Evidence " + score + "/100"
}

data class PhoneRiskResult(
    val displayNumber: String,
    val normalizedNumber: String,
    val score: Int,
    val verdict: Verdict,
    val reasons: List<String>,
    val recommendedAction: String,
    val shouldAutoBlock: Boolean = false,
    val trustedLocally: Boolean = false,
    val blockedLocally: Boolean = false,
    val reportedLocally: Boolean = false
) {
    val verdictLabel: String
        get() = when {
            blockedLocally -> "Blocked by you"
            trustedLocally -> "Trusted by you"
            verdict == Verdict.NO_STRONG_SIGNALS -> "Unknown caller · no scam evidence"
            verdict == Verdict.USE_CAUTION -> "Unusual calling pattern"
            reportedLocally -> "Previously reported by you"
            verdict == Verdict.SUSPECTED_SCAM -> "Suspicious call"
            else -> "High-risk call"
        }

    val headline: String
        get() = when {
            blockedLocally -> "You chose to block this caller"
            trustedLocally -> "You marked this caller as trusted"
            verdict == Verdict.NO_STRONG_SIGNALS -> "Unknown does not mean scam"
            verdict == Verdict.USE_CAUTION -> "Check the caller before sharing information"
            reportedLocally -> "This is based on your previous local report"
            else -> "Several concerning signals were found"
        }

    val scoreLabel: String
        get() = "Evidence " + score + "/100"
}
