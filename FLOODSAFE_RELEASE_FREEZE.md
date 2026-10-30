# FloodSafe Nepal v0.9.21 — Tested Source Freeze (2026-10-30)

## Frozen and verified
- Source branch: `release/floodsafe-v0.9.21-tested-freeze-20261030`
- Exact tested source commit: `07a470c56c359906816238a3a832ba61840d710a`
- Android source tree: `6ef8f67b45132b1f8d0226183d915bcfc2e0a729`
- Tested APK (separate `.preview` package): https://github.com/Pujan1234-hub/assigment/releases/download/floodsafe-v0921-last-reading-test-20261030/FloodSafe-Nepal-v0.9.21-LAST-READING-TEST.apk
- Verified by the owner on Android: original UI, map, stale gauge detail, OTA notice on/off, and Firebase *preview* push delivered to device.
- Confirmed by CI: Android debug unit tests, APK assembly and bundled asset verification. These are **not** a substitute for Nepal field tests.

## Freeze policy
Do not modify the frozen snapshot. Only user-approved release packaging, safety fixes, or store compliance changes may follow on a new branch after review.
The main branch's `floodsafe-android-app/` source has been promoted from the above frozen tree; all other projects and source directories remain preserved.
Legacy one-off FloodSafe APK build workflows from older v0.8.x variants were removed from active GitHub Actions configuration. Their historical content is preserved in `archive/floodsafe-main-before-v0921-freeze-20261030` and normal Git history. Old GitHub release assets were not deleted, and website download links were not changed.

## NOT YET a Play Store release
- The `.preview` TEST APK is not the signed Play Console bundle.
- A newly built, signed production/closed-testing AAB with package `com.pjbuilts.floodsafenepal` and a matching registered Firebase Android app remains to be produced and inspected.
- Complete Play Console privacy / background location / foreground service / data-safety declarations, and Nepal-side alert safety tests before production.
- Do not automatically publish a Play Store or public APK update from this freeze.
- Source data comes from verified DHM telemetry, BIPAD fallback; old gauge data must not be classified as current. Emergency alerts still require <=10-minute verified readings and <=2 km relevant-device location.

Recovery: https://github.com/Pujan1234-hub/assigment/tree/archive/floodsafe-main-before-v0921-freeze-20261030
