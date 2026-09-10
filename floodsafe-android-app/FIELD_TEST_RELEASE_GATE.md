# FloodSafe Nepal 0.6.0 — Field Test + Play Release Gate

This build is a release candidate. Do not publish to Production until every **P0 safety** check below passes on real Android phones.

## Tester setup

- Install the `FloodSafe-Nepal-FieldTest-0.6.0-APK` artifact.
- Use a phone physically in Nepal for the near-river test.
- Turn on precise location and notifications. Microphone is optional unless testing SATHI voice.
- Open FloodSafe Nepal, tap **मेरो हालको स्थान**, then enable **बाढी चेतावनी**.
- Do not manufacture or report a fake flood. The field test verifies location, distance, official-station freshness and notification delivery.

## P0 safety checks — all must PASS

| ID | Test | Expected result |
|---|---|---|
| P0-01 | Nepal current GPS | Current place is shown correctly and the app does not jump to an old/manual location. |
| P0-02 | Near a river/station | Nearby official river station(s) load with sensible distance and official observation time. |
| P0-03 | 2 km boundary | Only official warning/danger stations within 2 km are eligible for a proximity alert. A station beyond 2 km must not create a proximity notification. |
| P0-04 | Freshness | River observations older than the allowed freshness window must not trigger a warning notification. |
| P0-05 | App background | With alerts enabled, lock the screen and leave the app in background for at least 20 minutes. Local checks remain scheduled. |
| P0-06 | App swipe-away | Swipe the app away, wait at least 20 minutes, reopen it. No stale/false alert should appear. |
| P0-07 | Phone reboot | Reboot with alerts already enabled. Background WorkManager checks must be restored automatically. |
| P0-08 | Outside Nepal | On a phone physically outside Nepal, current-GPS river monitoring must not produce a Nepal nearby-river notification. |
| P0-09 | GPS stale | Disable location after a fresh current-GPS fix and wait over 5 minutes. The old coordinate must be invalidated for current-GPS proximity alerts. |
| P0-10 | Notification permission denied | Deny notifications. App must stay usable and must not crash or repeatedly prompt without a user action. |
| P0-11 | Offline/reconnect | Turn internet off, open app, then restore internet. UI must recover and live data must refresh without freezing. |
| P0-12 | Source integrity | Open several river/news source links and confirm displayed facts/timestamps agree with the linked source where comparable. |

## SATHI voice checks

1. Tap the microphone and ask a Nepali flood/weather question.
2. Confirm transcript appears and the answer is relevant to the selected/current location.
3. Enable “Ye Sathi”, background the app, speak the wake phrase and confirm either the app opens or the fallback notification appears.
4. Disable always-on voice and confirm listening stops.
5. Reboot the phone: voice listening must **not** silently start a microphone foreground service at boot. It may resume only after the user opens the app again and the saved setting is still enabled.

## Privacy + store checks

- `privacy.html` opens from the in-app **गोपनीयता र सुरक्षा** card.
- Android launcher icon renders correctly on an adaptive-icon device.
- App version reports 0.6.0 / versionCode 10.
- Play Console Data safety answers match actual location, microphone, Firebase messaging and network behavior.
- Foreground service declaration covers microphone and location use with a clear user-visible explanation/video.
- Store listing includes support contact, privacy-policy public URL, screenshots and the safety disclaimer.

## Result record

For each phone record: Android version, phone model, district/municipality (not exact home address), test date/time, P0 IDs passed/failed, screenshot for any failure, and the exact station name/time shown if testing near a river.

**Production gate:** 0 unresolved P0 failures. If a real warning/danger event is available during testing, verify one genuine proximity notification on a consenting tester phone before Production. Otherwise complete all non-hazard checks and keep the release in closed/open testing until a real warning delivery is observed.
