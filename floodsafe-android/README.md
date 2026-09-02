# FloodSafe Nepal beta APK

Installable **browser-based testing launcher**, not a full native Android app or
a Play Store release. Requires Android 8+ and an up-to-date browser. It opens:

https://pujan1234-hub.github.io/assigment/floodsafe-nepal/v25/

The live website is not modified or bundled. Existing river, news, human-impact,
GPS, map open/close and forecast logic runs at its original HTTPS origin.
Custom Tabs share the selected browser's site permissions and storage. If no
Custom Tabs provider is available, an ordinary browser opens the same URL.

## Important limitations

- Internet is required. This APK does not add offline data or native background tracking.
- GPS and notifications are opt-in website/browser permissions, not native APK permissions.
- Web push delivery depends on the browser, Android settings and backend. Real-device
  locked-screen/background delivery is still unverified. No guaranteed emergency alerts.
- Rain start/stop times are forecasts, not exact guarantees.
- Web map network-recovery end-to-end verification remains unresolved.
- Debug-signed beta only. Do not publish this build to Google Play. Separate future
  CI builds can use different debug keys and may require uninstalling the earlier beta.

## Reproducible build

JDK 17, Gradle 8.11.1, Android SDK 35, build tools 35.0.0:

```sh
cd floodsafe-android
gradle --no-daemon :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
```

The `Build FloodSafe Android Beta APK` workflow runs these checks, validates the
APK signature and uploads `FloodSafe-Nepal-Beta.apk` with its SHA-256 checksum.
Source-only Android additions live separately from the deployed website.

## First phone checks

1. Install and open the beta. Check the address is the HTTPS FloodSafe v25 site.
2. Tap current location and explicitly grant browser GPS permission. Confirm green marker.
3. Open/close 3D map; tap two different rivers. Reload: the map must start closed.
4. Toggle network off then on. Check connection state and eventual source refresh.
5. Opt into rain notifications and use the notification test. Also test locked screen;
   a foreground test alone does not prove background delivery or a real rain forecast.

No emulator/browser test claims to verify physical-device GPS or push delivery.
