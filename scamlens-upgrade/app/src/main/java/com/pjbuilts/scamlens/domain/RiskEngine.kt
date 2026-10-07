package com.pjbuilts.scamlens.domain

import java.net.URI
import java.util.Locale

object RiskEngine {
    private val urlRegex = Regex("""(?i)\b((?:https?://|www\.)[^\s<>]+|(?:[a-z0-9-]+\.)+(?:com|co\.uk|org|net|io|xyz|top|click|info|online|site|shop)(?:/[^\s<>]*)?)""")
    private val ipUrlRegex = Regex("""(?i)(?:https?://)?(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/|$)""")
    private val phoneCtaRegex = Regex("""(?i)\b(?:call|ring|whatsapp|text)\s+(?:us\s+|me\s+)?(?:now\s+)?(?:on\s+|at\s+)?\+?\d[\d\s().-]{6,}\d""")

    private val urgency = listOf(
        "urgent", "immediately", "act now", "within 24 hours", "within 2 hours", "final warning",
        "last chance", "account suspended", "account will be closed", "verify now", "action required",
        "delivery failed", "payment failed", "today only", "avoid arrest", "legal action"
    )
    private val credentials = listOf(
        "password", "passcode", " pin ", "one time password", " otp ", "verification code",
        "security code", "cvv", "card number", "bank login", "seed phrase", "recovery phrase",
        "memorable word", "online banking details"
    )
    private val payments = listOf(
        "gift card", "steam card", "google play card", "apple gift card", "wire transfer",
        "bank transfer", "send money", "pay a fee", "processing fee", "release fee",
        "redelivery fee", "customs fee", "advance payment", "pay by crypto", "new bank details"
    )
    private val crypto = listOf(
        "bitcoin", " btc ", "ethereum", " usdt ", "crypto", "wallet address",
        "guaranteed return", "double your money", "investment opportunity", "investment group",
        "trading signal", "guaranteed profit"
    )
    private val remote = listOf(
        "anydesk", "teamviewer", "remote desktop", "screen share", "install this app",
        "remote access", "quick support", "rustdesk", "quicksupport"
    )
    private val prize = listOf(
        "you have won", "claim your prize", "lottery", "selected for a reward", "free gift",
        "winner selected", "claim reward"
    )
    private val job = listOf(
        "work from home", "easy money", "daily commission", "task job", "pay to start",
        "training fee", "recharge task", "product boosting", "click task", "merchant task",
        "complete tasks", "earn commission"
    )
    private val impersonation = listOf(
        "hmrc", "tax refund", "police warrant", "bank fraud team", "fraud department",
        "amazon security", "microsoft support", "royal mail", "dhl delivery", "evri delivery",
        "dvla", "nhs", "visa security", "mastercard security"
    )
    private val delivery = listOf(
        "parcel fee", "missed delivery", "reschedule delivery", "redelivery",
        "delivery address", "customs charge", "package held"
    )
    private val invoice = listOf(
        "invoice attached", "outstanding invoice", "overdue invoice", "updated bank account",
        "change of bank details", "payment details changed"
    )

    private val shorteners = setOf("bit.ly", "tinyurl.com", "t.co", "cutt.ly", "is.gd", "rb.gy", "rebrand.ly", "shorturl.at")
    private val riskyTlds = setOf("zip", "mov", "click", "top", "xyz", "work", "support", "cam", "gq", "tk")
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
        val lower = " " + text.lowercase(Locale.ROOT) + " "
        val signals = mutableListOf<RiskSignal>()

        fun addHits(words: List<String>, title: String, detail: String, points: Int) {
            val hits = words.filter { lower.contains(it.lowercase(Locale.ROOT)) }.distinct()
            if (hits.isNotEmpty()) {
                signals += RiskSignal(title, detail + " (" + hits.take(3).joinToString() + ")", points)
            }
        }

        addHits(urgency, "Pressure / urgency", "The wording pushes you to act before checking", 14)
        addHits(credentials, "Sensitive information request", "It appears to request credentials or security codes", 28)
        addHits(payments, "Unusual payment request", "The payment method or fee is commonly abused in scams", 23)
        addHits(crypto, "Crypto / investment pattern", "Guaranteed-return or crypto-payment language raises fraud risk", 24)
        addHits(remote, "Remote access request", "Remote-control software can expose your device and accounts", 34)
        addHits(prize, "Prize / reward lure", "Unexpected reward language is a common social-engineering pattern", 18)
        addHits(job, "Suspicious job / task pattern", "The wording resembles pay-to-start or task scams", 22)
        addHits(impersonation, "Authority / brand claim", "The message invokes a trusted organisation or authority", 13)
        addHits(delivery, "Delivery-fee pattern", "Small parcel or redelivery fees are frequently used in phishing", 16)
        addHits(invoice, "Invoice / bank-detail change", "Unexpected payment-detail changes should be verified out of band", 24)

        if (Regex("""(?i)\b(?:£|\$|€)\s?\d+(?:[.,]\d{2})?\b""").containsMatchIn(text)) {
            signals += RiskSignal("Money mentioned", "A specific amount is involved; verify the request independently", 5)
        }
        if (phoneCtaRegex.containsMatchIn(text)) {
            signals += RiskSignal("Move conversation to a phone number", "Unexpected instructions to call or message a supplied number can bypass official channels", 8)
        }
        if (text.any { it == '\u200B' || it == '\u200C' || it == '\u200D' || it == '\u2060' }) {
            signals += RiskSignal("Hidden formatting characters", "Invisible characters can be used to evade filters or disguise text", 12)
        }

        val urls = urlRegex.findAll(text).map { cleanUrl(it.value) }.distinct().toList()
        urls.forEach { raw ->
            val host = getHost(raw)
            if (raw.contains("xn--", true)) signals += RiskSignal("Punycode domain", "Encoded domains can imitate familiar names", 30)
            if (ipUrlRegex.containsMatchIn(raw)) signals += RiskSignal("IP-address link", "Consumer services rarely use raw IP addresses for sign-in", 30)
            if (host in shorteners) signals += RiskSignal("Hidden link destination", "A shortener hides the final destination", 14)
            if (host.count { it == '.' } >= 3) signals += RiskSignal("Complex subdomain", "Many subdomain levels can disguise the real domain", 9)
            if (raw.contains("@")) signals += RiskSignal("Deceptive URL format", "An @ symbol can obscure the true destination", 28)
            if (host.length >= 45) signals += RiskSignal("Very long domain", "Long host names can be used to hide the important part of a domain", 8)
            if (host.count { it == '-' } >= 3) signals += RiskSignal("Hyphen-heavy domain", "Many hyphens can be a sign of a disposable or lookalike domain", 7)
            val tld = host.substringAfterLast('.', "")
            if (tld in riskyTlds) signals += RiskSignal("Higher-risk link ending", "This domain ending is frequently used for disposable or deceptive links", 10)
            if (Regex("""(?i)/(?:login|signin|verify|verification|secure|account|wallet|update)(?:/|\?|$)""").containsMatchIn(raw)) {
                signals += RiskSignal("Login / verification link", "The link asks you to authenticate or verify an account", 9)
            }

            brandDomains.forEach { (brand, officialDomains) ->
                if (lower.contains(brand) && host.isNotBlank()) {
                    val official = officialDomains.any { host == it || host.endsWith("." + it) }
                    if (!official) {
                        signals += RiskSignal(
                            "Brand/domain mismatch",
                            "The message mentions " + brand.replaceFirstChar { it.uppercaseChar() } + ", but the link host is " + host,
                            36
                        )
                    }
                }
            }
        }

        if (urls.isNotEmpty() && signals.none { it.title == "Brand/domain mismatch" }) {
            signals += RiskSignal("External link present", "Important accounts are safer to open from the official app or a saved bookmark", 5)
        }

        val unique = signals.distinctBy { it.title + "|" + it.detail }.toMutableList()
        val credentialHit = unique.any { it.title == "Sensitive information request" }
        val urgencyHit = unique.any { it.title == "Pressure / urgency" }
        val mismatchHit = unique.any { it.title == "Brand/domain mismatch" }
        val paymentHit = unique.any { it.title == "Unusual payment request" }
        val impersonationHit = unique.any { it.title == "Authority / brand claim" }
        val remoteHit = unique.any { it.title == "Remote access request" }

        var score = unique.sumOf { it.points }
        if (credentialHit && urgencyHit) score += 12
        if (credentialHit && mismatchHit) score += 18
        if (impersonationHit && paymentHit) score += 12
        if (urgencyHit && paymentHit) score += 9
        if (remoteHit && (paymentHit || credentialHit)) score += 18
        if (unique.count { it.points >= 20 } >= 2) score += 8
        if (unique.size >= 4) score += 6
        score = score.coerceIn(0, 100)

        val verdict = when {
            score >= 78 -> Verdict.HIGH_RISK
            score >= 52 -> Verdict.SUSPECTED_SCAM
            score >= 26 -> Verdict.USE_CAUTION
            else -> Verdict.NO_STRONG_SIGNALS
        }
        val level = when (verdict) {
            Verdict.HIGH_RISK -> RiskLevel.CRITICAL
            Verdict.SUSPECTED_SCAM -> RiskLevel.HIGH
            Verdict.USE_CAUTION -> RiskLevel.MEDIUM
            Verdict.NO_STRONG_SIGNALS -> RiskLevel.LOW
        }
        val category = when {
            remoteHit -> "Remote-access scam pattern"
            unique.any { it.title == "Suspicious job / task pattern" } -> "Job / task scam pattern"
            unique.any { it.title == "Crypto / investment pattern" } -> "Investment / crypto scam pattern"
            mismatchHit -> "Impersonation / phishing pattern"
            unique.any { it.title == "Invoice / bank-detail change" } -> "Invoice / payment redirection pattern"
            unique.any { it.title == "Delivery-fee pattern" } -> "Delivery phishing pattern"
            unique.any { it.title == "Prize / reward lure" } -> "Prize / reward scam pattern"
            credentialHit -> "Credential phishing pattern"
            score >= 26 -> "Suspicious communication"
            else -> "No strong pattern found"
        }

        val actions = buildList {
            when (verdict) {
                Verdict.HIGH_RISK -> add("Stop. Do not click, pay, call the supplied number, install apps, or share security codes.")
                Verdict.SUSPECTED_SCAM -> add("Do not act from this message. Verify the sender through a trusted channel first.")
                Verdict.USE_CAUTION -> add("Pause and verify independently before replying, paying, signing in, or downloading anything.")
                Verdict.NO_STRONG_SIGNALS -> add("No strong pattern was found, but verify anything involving money, passwords, codes, or urgent requests.")
            }
            if (urls.isNotEmpty()) add("Open the organisation from its official app or type the known website yourself.")
            if (credentialHit) add("Never share passwords, PINs, OTPs, recovery phrases, or full card details.")
            if (remoteHit) add("Do not install remote-control software for an unsolicited caller or message.")
            if (paymentHit) add("Confirm payment requests using contact details you already trust, not details in this message.")
        }.distinct()

        return ScanResult(
            rawInput = text,
            score = score,
            level = level,
            verdict = verdict,
            category = category,
            signals = unique.sortedByDescending { it.points },
            actions = actions,
            source = source
        )
    }

    private fun cleanUrl(value: String): String =
        value.trim().trimEnd('.', ',', ';', ':', ')', ']', '}', '!', '?')

    private fun getHost(value: String): String {
        val normalized = when {
            value.startsWith("www.", true) -> "https://" + value
            value.startsWith("http://", true) || value.startsWith("https://", true) -> value
            else -> "https://" + value
        }
        return try {
            URI(normalized).host?.lowercase(Locale.ROOT)?.removePrefix("www.") ?: ""
        } catch (_: Exception) {
            ""
        }
    }
}
