package com.pjbuilts.scamlens.domain

enum class RiskLevel { LOW, MEDIUM, HIGH, CRITICAL }
enum class Verdict { NO_STRONG_SIGNALS, USE_CAUTION, SUSPECTED_SCAM, HIGH_RISK }
enum class ScanSource { MANUAL, SHARED, SCREENSHOT, QR, NOTIFICATION, PHONE, CALL }

data class RiskSignal(
    val title: String,
    val detail: String,
    val points: Int
)

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
            Verdict.NO_STRONG_SIGNALS -> "No strong scam signals detected"
            Verdict.USE_CAUTION -> "Unverified · use caution"
            Verdict.SUSPECTED_SCAM -> "Suspected scam"
            Verdict.HIGH_RISK -> "High risk · likely scam"
        }
}

data class PhoneRiskResult(
    val displayNumber: String,
    val normalizedNumber: String,
    val score: Int,
    val verdict: Verdict,
    val reasons: List<String>,
    val recommendedAction: String,
    val shouldAutoBlock: Boolean = false
) {
    val verdictLabel: String
        get() = when (verdict) {
            Verdict.NO_STRONG_SIGNALS -> "No strong scam signals"
            Verdict.USE_CAUTION -> "Unverified caller"
            Verdict.SUSPECTED_SCAM -> "Suspected scam call"
            Verdict.HIGH_RISK -> "High-risk scam call"
        }
}
