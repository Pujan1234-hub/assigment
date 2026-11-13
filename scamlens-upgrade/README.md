# ScamLens by PJBUILTS — v1.3.0 beta 2

This is an incremental upgrade of the native Android v1.2.1 app, package `com.pjbuilts.scamlens`.

## Completed — Step 1: false-positive protection

- Unknown and withheld callers no longer count as scam evidence.
- Repeated calls without other evidence do not auto-block legitimate recruiters.
- Manual blocks mean **blocked by you**, not **proven fraud**.
- Reports are clearly labelled local/personal, not crowd-verified.
- Default caller notifications are quiet unless a warning has actual evidence.
- Mentioning a brand while linking elsewhere is not, by itself, phishing.
- Notification Guard requires a stronger suspicious pattern before interrupting.
- UI labels distinguish lack of evidence from verified caller identity.
- JUnit regression cases cover genuine unknown callers, reported repeat callers,
  Google/article links and actual phishing examples.

## Beta 2 UI fix

- Protection and Settings toggles now bind to Compose observable state.
- Switches redraw immediately, with no back-navigation needed, while values persist in SharedPreferences.
- Notification Guard status updates in-place as its switch changes.

## Next steps

1. Add a consented caller-ID provider interface and verified-business name lookup.
   The current project has **no licensed reverse lookup database**: do not display
   invented caller names or claim that every UK number can be identified.
2. Add a provenance-aware reputation service with provider attribution and caching.
3. Improve the call UI / notifications and privacy controls.
4. Test real Android call screening on Samsung devices; it must respond within five seconds.

Existing message/link scan, OCR, QR, local history, report/trust/block actions,
CallScreeningService and Notification Guard remain in place.
