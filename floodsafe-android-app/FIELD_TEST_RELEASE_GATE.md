# FloodSafe Nepal 0.6.1 — Field Test + Play Release Gate

This build is a release candidate. Do not publish to Production until every **P0 safety** check below passes on real Android phones.

## Tester setup

- Install the `FloodSafe-Nepal-FieldTest-0.6.1-APK` artifact.
- Use a phone physically in Nepal for the near-river/station test. The tester does **not** need to approach a dangerous river bank or enter flood water; a safe location near an official station is enough.
- Turn on precise location and notifications. Microphone is optional unless testing SATHI voice.
- Open FloodSafe Nepal, tap **मेरो हालको स्थान**, then enable **बाढी चेतावनी**.
- When FloodSafe explains background safety monitoring, allow background location. On Android 11+ the first permission sheet normally only offers while-in-use; follow the app to Android Settings → Permissions → Location and choose the system's **Allow all the time** option when available.
- Confirm the ongoing **FloodSafe Nepal सुरक्षा निगरानी चालु छ** notification appears while background monitoring is active.
- Do not manufacture or report a fake flood. The field test verifies location, distance, official-station freshness and notification delivery.

## P0 safety checks — all must PASS

| ID | Test | Expected result |
|---|---|---|
| P0-01 | Nepal current GPS | Current place is shown correctly and the app does not jump to an old/manual location. |
| P0-02 | Near a river/station | Nearby official river station(s) load with sensible distance and official observation time. Stay in a safe public/home location; do not approach hazardous water. |
| P0-03 | 2 km boundary | Only official warning/danger stations within 2 km are eligible for a proximity alert. A station beyond 2 km must not create a proximity notification. |
| P0-04 | Freshness | River observations older than the allowed freshness window must not trigger a warning notification. |
| P0-05 | Alert state persistence | Turn **Warning Alert ON**, press Home, lock/unlock the phone, swipe the UI away, then reopen. The user's saved alert choice must remain ON unless the user explicitly turned it off or notification permission was revoked. |
| P0-06 | App background | With alerts enabled and background location allowed, lock the screen and leave the app in background for at least 20 minutes. The ongoing FloodSafe monitoring notification remains and current-device location continues to refresh. |
| P0-07 | App swipe-away | Swipe the app away, wait at least 20 minutes, then reopen. The foreground location monitor + FCM/WorkManager paths must remain available and no stale/false alert should appear. |
| P0-08 | Phone reboot | Reboot with alerts already enabled and background location allowed. WorkManager + FCM restore automatically; native continuous location monitoring should restore when Android permits it. |
| P0-09 | Outside Nepal | On a phone physically outside Nepal, current location may continue local rain/weather monitoring but must not produce a Nepal nearby-river notification. |
| P0-10 | GPS stale | Disable location after a fresh current-GPS fix and wait over 5 minutes. The old coordinate must be invalidated for current-GPS rain/river matching without silently changing the user's Warning Alert setting to OFF. |
| P0-11 | Notification permission denied | Deny/revoke notifications. App must stay usable and must not crash or repeatedly prompt without a user action; notification delivery is unavailable until permission is restored. |
| P0-12 | Offline/reconnect | Turn internet off, open app, then restore internet. UI must recover and live data must refresh without freezing. |
| P0-13 | Movement/current location | With background monitoring active, move a meaningful distance in a safe area (or use a controlled emulator/mock-location test) and confirm the current-device monitoring point updates rather than retaining the old location. |
| P0-14 | Source integrity | Open several river/news source links and confirm displayed facts/timestamps agree with the linked source where comparable. |
| P0-15 | Genuine event delivery | If an official warning/danger exists near a consenting tester, verify the genuine notification uses the current location and station data. Never create a fake public hazard to force this test. |

## Important Android limit

An explicit Android **Force stop** is different from simply closing/swiping the app. After the user chooses Force stop in Android Settings, the OS intentionally prevents normal background components from running until the user opens the app again. FloodSafe must not claim to bypass that OS safety control.

## SATHI voice checks

1. Tap the microphone and ask a Nepali flood/weather question.
2. Confirm transcript appears and the answer is relevant to the selected/current location.
3. Enable “Ye Sathi”, background the app, speak the wake phrase and confirm either the app opens or the fallback notification appears.
4. Disable always-on voice and confirm listening stops.
5. Reboot the phone: voice listening must **not** silently start a microphone foreground service at boot. It may resume only after the user opens the app again and the saved setting is still enabled.

## Privacy + store checks

- `privacy.html` opens from the in-app **गोपनीयता र सुरक्षा** card and explains background location/foreground-service behavior.
- Android launcher icon renders correctly on an adaptive-icon device.
- App version reports 0.6.1 / versionCode 11.
- Play Console Data safety answers match actual location, background location, microphone, Firebase messaging and network behavior.
- Foreground service declaration covers microphone and location use with a clear user-visible explanation/video where Play Console requires it.
- Store listing includes support contact, privacy-policy public URL, screenshots and the safety disclaimer.

## Result record

For each phone record: Android version, phone model, district/municipality (not exact home address), test date/time, P0 IDs passed/failed, screenshot for any failure, and the exact station name/time shown if testing near a river.

**Production gate:** 0 unresolved P0 failures. If a real warning/danger event is available during testing, verify one genuine proximity notification on a consenting tester phone before Production. Otherwise complete all non-hazard checks and keep the release in closed/open testing until a real warning delivery is observed.
