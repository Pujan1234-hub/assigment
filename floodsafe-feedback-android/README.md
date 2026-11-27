# FloodSafe Feedback v1.0.0 — private Android admin

A separate native feedback inbox for the existing FloodSafe Nepal submissions.

- Directly calls https://camkoacuokffryyrygda.supabase.co/functions/v1/feedback-api with x-admin-token. No dependence on the website admin page being open.
- Live feedback list, search, status filters, New / Reviewing / Fixed / Closed counts.
- Detail view with reporter message, contact, app version, device info and screenshot link.
- Update feedback status and add an admin note.
- Token is entered by owner and held only in memory. Closing or locking the app signs out. Nothing sensitive is embedded in the APK.
- INTERNET is the only Android permission. The original FloodSafe Nepal v0.9.23 and its signing identity are untouched.

Build: GitHub Actions, Java 17, Android Gradle 8.10.1, Gradle 8.11.1, API 35.
Package: com.pjbuilts.floodsafefeedback
The first APK uses an independent one-time signing key; future updates need persistent signing or fresh installation.

If the private admin token has been lost, this APK cannot recover or bypass it. Use the original feedback Supabase project to reset it.
