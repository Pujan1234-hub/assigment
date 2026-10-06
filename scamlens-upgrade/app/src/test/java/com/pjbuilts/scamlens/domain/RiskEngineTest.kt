package com.pjbuilts.scamlens.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class RiskEngineTest {
    @Test
    fun lowRiskIsNeverDescribedAsSafe() {
        val r = RiskEngine.analyse("Hello, are we still meeting tomorrow?")
        assertEquals(Verdict.NO_STRONG_SIGNALS, r.verdict)
        assertTrue(r.verdictLabel.contains("No strong"))
    }

    @Test
    fun phishingCompoundSignalsEscalate() {
        val r = RiskEngine.analyse("URGENT: your PayPal account will be closed. Verify password and OTP now at https://paypal.security-check.example.com")
        assertTrue(r.score >= 75)
        assertEquals(Verdict.HIGH_RISK, r.verdict)
        assertTrue(r.signals.any { it.title == "Brand/domain mismatch" })
    }

    @Test
    fun remoteAccessAndPaymentAreHighConcern() {
        val r = RiskEngine.analyse("Install AnyDesk now and pay the release fee so we can secure your bank account")
        assertTrue(r.score >= 50)
    }

    @Test
    fun reportedCallerGetsStrongReaction() {
        val r = PhoneRiskEngine.analyse("+447700900123", locallyReported = true)
        assertTrue(r.score >= 50)
        assertTrue(r.verdict == Verdict.SUSPECTED_SCAM || r.verdict == Verdict.HIGH_RISK)
    }

    @Test
    fun blockedCallerGetsMaximumRisk() {
        val r = PhoneRiskEngine.analyse("+447700900123", locallyBlocked = true)
        assertEquals(100, r.score)
        assertEquals(Verdict.HIGH_RISK, r.verdict)
    }

    @Test
    fun withheldCallerIsNotShownAsSafe() {
        val r = PhoneRiskEngine.analyse(null)
        assertTrue(r.score >= 50)
        assertEquals(Verdict.SUSPECTED_SCAM, r.verdict)
    }
}
