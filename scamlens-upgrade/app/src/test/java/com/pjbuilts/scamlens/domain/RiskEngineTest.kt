package com.pjbuilts.scamlens.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class RiskEngineTest {
    @Test fun ordinaryConversationHasNoStrongScamSignals() {
        val r = RiskEngine.analyse("Hello, are we still meeting tomorrow?")
        assertEquals(Verdict.NO_STRONG_SIGNALS, r.verdict)
    }

    @Test fun realPayPalPhishingStillEscalates() {
        val r = RiskEngine.analyse("URGENT: your PayPal account will be closed. Verify password and OTP now at https://paypal.security-check.example.com")
        assertTrue(r.score >= 75)
        assertEquals(Verdict.HIGH_RISK, r.verdict)
        assertTrue(r.signals.any { it.title == "Brand/domain mismatch" })
    }

    @Test fun mentioningGoogleWithUnrelatedLinkIsNotImpersonation() {
        val r = RiskEngine.analyse("Interesting Google news discussed at https://chatgpt.com")
        assertEquals(Verdict.NO_STRONG_SIGNALS, r.verdict)
        assertFalse(r.signals.any { it.title == "Brand/domain mismatch" })
    }

    @Test fun genericBrandCommentaryDoesNotTriggerScamAlert() {
        val r = RiskEngine.analyse("Check this article about Google: https://chatgpt.com")
        assertFalse(r.signals.any { it.title == "Brand/domain mismatch" })
        assertTrue(r.score < 52)
    }

    @Test fun remoteAccessWithPaymentIsHighConcern() {
        val r = RiskEngine.analyse("Install AnyDesk now and pay the release fee so we can secure your bank account")
        assertTrue(r.score >= 50)
    }

    @Test fun reportedCallerShowsLocalSourceOfEvidence() {
        val r = PhoneRiskEngine.analyse("+447700900123", locallyReported = true)
        assertEquals(Verdict.SUSPECTED_SCAM, r.verdict)
        assertTrue(r.reportedLocally)
        assertFalse(r.shouldAutoBlock)
    }

    @Test fun ordinaryUnknownRecruiterIsNotAccusedOfScam() {
        val r = PhoneRiskEngine.analyse("+447700900123")
        assertEquals(0, r.score)
        assertEquals(Verdict.NO_STRONG_SIGNALS, r.verdict)
        assertTrue(r.verdictLabel.contains("Unknown"))
        assertFalse(r.shouldAutoBlock)
    }

    @Test fun repeatedUnknownCallerIsNotAutomaticallyBlocked() {
        val r = PhoneRiskEngine.analyse("+447700900123", repeatCallsInTenMinutes = 4, autoBlockHighRisk = true)
        assertTrue(r.score < 25)
        assertEquals(Verdict.NO_STRONG_SIGNALS, r.verdict)
        assertFalse(r.shouldAutoBlock)
    }

    @Test fun userReportedRepeatCallerMayBeBlockedWhenOptedIn() {
        val r = PhoneRiskEngine.analyse("+447700900123", locallyReported = true, repeatCallsInTenMinutes = 4, autoBlockHighRisk = true)
        assertEquals(Verdict.HIGH_RISK, r.verdict)
        assertTrue(r.shouldAutoBlock)
    }

    @Test fun highRiskDeliveryPhishingStillRecognised() {
        val r = RiskEngine.analyse("Royal Mail: missed delivery. Pay redelivery fee now at https://royalmail-redelivery-check.xyz/login")
        assertTrue(r.score >= 52)
        assertTrue(r.verdict == Verdict.SUSPECTED_SCAM || r.verdict == Verdict.HIGH_RISK)
    }

    @Test fun blockedCallerIsNotAutomaticallyLabelledFraud() {
        val r = PhoneRiskEngine.analyse("+447700900123", locallyBlocked = true)
        assertEquals(0, r.score)
        assertTrue(r.blockedLocally)
        assertTrue(r.shouldAutoBlock)
        assertTrue(r.verdictLabel.contains("Blocked"))
    }

    @Test fun withheldNumberIsUnknownNotFraud() {
        val r = PhoneRiskEngine.analyse(null)
        assertEquals(0, r.score)
        assertEquals(Verdict.NO_STRONG_SIGNALS, r.verdict)
    }
}
