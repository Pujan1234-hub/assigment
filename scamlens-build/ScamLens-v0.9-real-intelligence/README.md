# ScamLens by PJBUILTS — v0.9 Real Intelligence Beta

Native Android / Kotlin / Jetpack Compose anti-scam app focused on useful real-world reactions, not score-only output.

## v0.9 upgrades
- Fixed the legacy regex engine so urgency, OTP/PIN, payment, phone, money and URL signals are actually detected correctly.
- Stronger compound-risk logic and scam categories: bank safe-account, authority impersonation, delivery phishing, remote access, task/job scams, crypto/investment and credential phishing.
- Android Call Screening role with fast incoming caller checks.
- Live anonymous ScamLens community reputation for phone numbers and domains using the PJBUILTS Supabase `scamlens-intel` service.
- Optional auto-block and optional silence for high-risk callers.
- High-priority caller warning notification with verdict + reasons, not only a number score.
- Message/link scanner combines on-device analysis, PhishTank verification and ScamLens community reports.
- Notification Guard analyses notification text and enriches suspicious links with live intelligence.
- Screenshot OCR, QR scanner, share-to-ScamLens, caller check, report/block flow and persistent local history.
- Anonymous community reports use a one-way SHA-256 device hash; no contact list, SMS or call-log upload.
- PJBUILTS intro animation retained.

## Product rule
A low score is never presented as proof that something is safe. ScamLens displays a verdict, reasons and recommended actions, with the numeric score treated as supporting evidence.

## Android / Play policy approach
The app does not request restricted SMS or Call Log permissions. Incoming-call protection uses Android's Call Screening role. Message protection uses user-enabled Notification Access.

## Build
JDK 17, Android SDK 36, Gradle 8.13.
