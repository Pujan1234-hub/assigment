package com.pjbuilts.scamlens.domain

import android.content.Context

object PhoneRiskEngine {
    fun normalize(number: String?): String = number.orEmpty().trim().replace(Regex("[^+0-9]"), "")

    fun analyse(context: Context, number: String?, communityReports: Int? = null): ScanResult {
        val raw = number.orEmpty().trim()
        val clean = normalize(raw)
        val signals = mutableListOf<RiskSignal>()
        val store = ProtectionStore(context)
        val localReports = store.reportCount("phone:$clean")
        val cachedReports = communityReports ?: store.communityReportCount(clean)
        val blocked = store.isBlocked(clean)

        if (raw.isBlank() || raw.equals("unknown", true) || raw.equals("private", true) || raw.equals("withheld", true)) {
            signals += RiskSignal("Hidden caller identity", "The caller number is unavailable. Do not rely on the caller's claimed identity.", 30)
        }
        if (blocked) {
            signals += RiskSignal("Blocked by you", "You previously added this number to ScamLens' block list.", 82, "Your protection list")
        }
        if (localReports > 0) {
            signals += RiskSignal("Reported by you", "You previously reported this number $localReports time${if (localReports == 1) "" else "s"}.", 64, "Your reports")
        }
        if (cachedReports > 0) {
            val pts = when {
                cachedReports >= 20 -> 70
                cachedReports >= 10 -> 58
                cachedReports >= 5 -> 46
                cachedReports >= 2 -> 30
                else -> 18
            }
            signals += RiskSignal(
                "Community scam reports",
                "$cachedReports ScamLens community report${if (cachedReports == 1) "" else "s"} found for this number.",
                pts,
                "ScamLens live community intelligence"
            )
        }
        if (clean.length in 1..6) {
            signals += RiskSignal("Very short caller ID", "The caller ID format is unusual and should be verified before trusting it.", 14)
        }
        if (clean.startsWith("+")) {
            signals += RiskSignal("International caller ID", "An international number is not automatically suspicious, but unexpected overseas calls deserve verification.", 3)
        }
        if (clean.startsWith("+44") && clean.length !in 12..13) {
            signals += RiskSignal("Unusual UK number format", "This caller ID does not match a typical UK international number length.", 10)
        }
        if (clean.startsWith("00")) {
            signals += RiskSignal("International dialling prefix", "The caller ID uses an international dialling prefix; verify unexpected calls independently.", 3)
        }
        if (clean.length >= 7 && !blocked && localReports == 0 && cachedReports == 0) {
            signals += RiskSignal(
                "Caller identity unverified",
                "ScamLens has no trusted identity or community scam report for this number yet. New scam numbers can have no history.",
                8,
                "ScamLens caller screening"
            )
        }

        val score = signals.sumOf { it.points }.coerceIn(0, 100)
        val level = when {
            score >= 78 -> RiskLevel.CRITICAL
            score >= 50 -> RiskLevel.HIGH
            score >= 24 -> RiskLevel.MEDIUM
            else -> RiskLevel.LOW
        }
        val verdict = when (level) {
            RiskLevel.CRITICAL -> "Likely scam / blocked caller"
            RiskLevel.HIGH -> "High-risk caller — do not trust the identity"
            RiskLevel.MEDIUM -> "Caller needs verification"
            RiskLevel.LOW -> "Unknown reputation — verify the caller independently"
        }
        val category = when {
            blocked -> "Your blocked caller"
            cachedReports >= 5 -> "Community-reported scam caller"
            localReports > 0 -> "Previously reported caller"
            clean.isBlank() -> "Hidden caller"
            else -> "Caller reputation check"
        }
        val actions = buildList {
            if (level >= RiskLevel.HIGH) add("Do not give this caller security codes, passwords, card details or remote access.")
            add("If they claim to be your bank, police, HMRC or another organisation, hang up and call back using a trusted official number.")
            add("Do not transfer money because a caller says your account is unsafe.")
        }
        return ScanResult(raw.ifBlank { "Unknown caller" }, score, level, verdict, category, signals.sortedByDescending { it.points }, actions)
    }
}
