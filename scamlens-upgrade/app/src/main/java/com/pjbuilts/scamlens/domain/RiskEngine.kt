package com.pjbuilts.scamlens.domain

import java.net.URI
import java.util.Locale

object RiskEngine {
    private val urlRegex = Regex("""(?i)\b((?:https?://|www\.)[^\s<>]+)""")
    private val ipUrlRegex = Regex("""(?i)(?:https?://)?(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/|$)""")

    private val urgency = listOf(
        "urgent", "immediately", "act now", "within 24 hours", "final warning", "last chance",
        "account suspended", "account will be closed", "verify now", "action required", "delivery failed"
    )
    private val credentials = listOf(
        "password", "passcode", " pin ", "one time password", " otp ", "verification code",
        "security code", "cvv", "card number", "bank login", "seed phrase", "recovery phrase"
    )
    private val payments = listOf(
        "gift card", "steam card", "google play card", "apple gift card", "wire transfer",
        "bank transfer", "send money", "pay a fee", "processing fee", "release fee",
        "redelivery fee", "customs fee", "advance payment"
    )
    private val crypto = listOf(
        "bitcoin", " btc ", "ethereum", " usdt ", "crypto", "wallet address",
        "guaranteed return", "double your money", "investment opportunity"
    )
    private val remote = listOf(
        "anydesk", "teamviewer", "remote desktop", "screen share", "install this app",
        "remote access", "quick support", "rustdesk"
    )
    private val prize = listOf("you have won", "claim your prize", "lottery", "selected for a reward", "free gift")
    private val job = listOf(
        "work from home", "easy money", "daily commission", "task job", "pay to start",
        "training fee", "recharge task", "product boosting", "click task"
    )
    private val impersonation = listOf(
        "hmrc", "tax refund", "police warrant", "bank fraud team", "fraud department",
        "amazon security", "microsoft support", "royal mail", "dhl delivery", "evri delivery", "dvla"
    )
    private val shorteners = setOf("bit.ly", "tinyurl.com", "t.co", "cutt.ly", "is.gd", "rb.gy", "rebrand.ly")
    private val brandDomains = mapOf(
        "paypal" to setOf("paypal.com", "paypal.co.uk"),
        "amazon" to setOf("amazon.com", "amazon.co.uk"),
        "apple" to setOf("apple.com", "icloud.com"),
        "microsoft" to setOf("microsoft.com", "live.com", "outlook.com"),
        "google" to setOf("google.com", "gmail.com"),
        "royal mail" to setOf("royalmail.com"),
        "hmrc" to setOf("gov.uk"),
        "dvla" to setOf("gov.uk"),
        "nhs" to setOf("nhs.uk")
    )

    fun analyse(input: String, source: ScanSource = ScanSource.MANUAL): ScanResult {
        val text = input.trim()
        val lower = " \${text.lowercase(Locale.ROOT)} "
        val signals = mutableListOf<RiskSignal>()

        fun addHits(words: List<String>, title: String, detail: String, points: Int) {
            val hits = words.filter { lower.contains(it.lowercase(Locale.ROOT)) }
            if (hits.isNotEmpty()) {
                signals += RiskSignal(title, "$detail (\${hits.take(3).joinToString()})", points)
            }
        }

        addHits(urgency, "Pressure / urgency", "The wording pushes you to act before checking", 15)
        addHits(credentials, "Sensitive information request", "It appears to request credentials or security codes", 24)
        addHits(payments, "Unusual payment request", "The payment method or fee is commonly abused in scams", 22)
        addHits(crypto, "Crypto / investment pattern", "Crypto or guaranteed-return language increases fraud risk", 22)
        addHits(remote, "Remote access request", "Remote-control software can expose your device and accounts", 30)
        addHits(prize, "Prize / reward lure", "Unexpected reward language is a common social-engineering pattern", 17)
        addHits(job, "Suspicious job / task pattern", "The wording resembles pay-to-start or task scams", 20)
        addHits(impersonation, "Authority / brand impersonation pattern", "The message invokes a trusted organisation or authority", 12)

        if (Regex("""(?i)\b(?:£|\$|€)\s?\d+(?:[.,]\d{2})?\b""").containsMatchIn(text)) {
            signals += RiskSignal("Money mentioned", "A specific amount is involved; verify the request independently", 5)
        }

        val urls = urlRegex.findAll(text).map { cleanUrl(it.value) }.distinct().toList()
        urls.forEach { raw ->
            val host = getHost(raw)
            if (raw.contains("xn--", true)) signals += RiskSignal("Punycode domain", "Encoded domains can imitate familiar names", 22)
            if (ipUrlRegex.containsMatchIn(raw)) signals += RiskSignal("IP-address link", "Consumer services rarely use raw IP addresses for sign-in", 26)
            if (host in shorteners) signals += RiskSignal("Hidden link destination", "A shortener hides the final destination", 12)
            if (host.count { it == '.' } >= 3) signals += RiskSignal("Complex subdomain", "Many subdomain levels can disguise the real domain", 8)
            if (raw.contains("@")) signals += RiskSignal("Deceptive URL format", "An @ symbol can obscure the true destination", 18)

            brandDomains.forEach { (brand, officialDomains) ->
                if (lower.contains(brand) && host.isNotBlank()) {
                    val official = officialDomains.any { host == it || host.endsWith(".$it") }
                    if (!official) {
                        signals += RiskSignal(
                            "Brand/domain mismatch",
                            "The message mentions \${brand.replaceFirstChar { it.uppercase() }}, but the link host is $host",
                            32
                        )
                    }
                }
            }
        }
        if (urls.isNotEmpty() && signals.none { it.title == "Brand/domain mismatch" }) {
            signals += RiskSignal("External link present", "Use the official app or a saved bookmark for important accounts", 5)
        }

        val credentialHit = signals.any { it.title == "Sensitive information request" }
        val urgencyHit = signals.any { it.title == "Pressure / urgency" }
        val mismatchHit = signals.any { it.title == "Brand/domain mismatch" }
        val paymentHit = signals.any { it.title == "Unusual payment request" }
        val impersonationHit = signals.any { it.title == "Authority / brand impersonation pattern" }

        var score = signals.sumOf { it.points }
        if (credentialHit && urgencyHit) score += 12
        if (credentialHit && mismatchHit) score += 15
        if (impersonationHit && paymentHit) score += 12
        if (urgencyHit && paymentHit) score += 8
        score = score.coerceIn(0, 100)

        val verdict = when {
            score >= 75 -> Verdict.HIGH_RISK
            score >= 50 -> Verdict.SUSPECTED_SCAM
            score >= 25 -> Verdict.USE_CAUTION
            else -> Verdict.NO_STRONG_SIGNALS
        }
        val level = when (verdict) {
            Verdict.HIGH_RISK -> RiskLevel.CRITICAL
            Verdict.SUSPECTED_SCAM -> RiskLevel.HIGH
            Verdict.USE_CAUTION -> RiskLevel.MEDIUM
            Verdict.NO_STRONG_SIGNALS -> RiskLevel.LOW
        }
        val category = when {
            signals.any { it.title == "Remote access request" } -> "Remote-access scam pattern"
            signals.any { it.title == "Suspicious job / task pattern" } -> "Job / task scam pattern"
            signals.any { it.title == "Crypto / investment pattern" } -> "Investment / crypto scam pattern"
            mismatchHit -> "Impersonation / phishing pattern"
            signals.any { it.title == "Prize / reward lure" } -> "Prize / reward scam pattern"
            credentialHit -> "Credential phishing pattern"
            score >= 25 -> "Suspicious communication"
            else -> "No strong pattern found"
        }
        val actions = buildList {
            if (verdict == Verdict.HIGH_RISK || verdict == Verdict.SUSPECTED_SCAM) {
                add("Do not click links, send money, install apps, or share security codes from this message.")
            }
            if (urls.isNotEmpty()) add("Open the organisation from its official app or type the known website yourself.")
            if (credentialHit) add("Never share passwords, PINs, OTPs, recovery phrases, or full card details.")
            if (signals.any { it.title == "Remote access request" }) add("Do not install remote-control software for an unsolicited caller.")
            add("Verify independently using a trusted contact method you already know.")
        }

        return ScanResult(
            rawInput = text,
            score = score,
            level = level,
            verdict = verdict,
            category = category,
            signals = signals.distinctBy { it.title + it.detail }.sortedByDescending { it.points },
            actions = actions,
            source = source
        )
    }

    private fun cleanUrl(value: String) =
        value.trim().trimEnd('.', ',', ';', ':', ')', ']', '}', '!', '?')

    private fun getHost(value: String): String {
        val normalized = when {
            value.startsWith("www.", true) -> "https://$value"
            value.startsWith("http://", true) || value.startsWith("https://", true) -> value
            else -> "https://$value"
        }
        return try {
            URI(normalized).host?.lowercase(Locale.ROOT)?.removePrefix("www.") ?: ""
        } catch (_: Exception) {
            ""
        }
    }
}
