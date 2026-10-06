package com.pjbuilts.scamlens.domain

object PrivacyRedactor {
    private val email = Regex("""[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}""")
    private val phone = Regex("""(?<!\d)(?:\+?\d[\d ()-]{7,}\d)(?!\d)""")
    private val postcode = Regex("""(?i)\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b""")
    fun redact(text: String): String = text
        .replace(email, "[email hidden]")
        .replace(phone, "[phone hidden]")
        .replace(postcode, "[postcode hidden]")
}
