# FloodSafe Nepal Android app — 0.2.0 beta

This hybrid Android app bundles the FloodSafe UI and reference data from the
laptop ZIP (web source commit `949e2af4af6436a802fb68635f974be2a5c4d9a0`). It opens
inside its own Android WebView. Android 8 or newer is required. River readings,
news, weather and satellite map tiles still need internet. Bundled snapshots
retain their original observation dates and existing freshness checks.

The app requests foreground Android location permission only when the user asks
for current location. Both approximate and precise grants are supported. There
is no JavaScript/native bridge, external pages stay outside the app, file/content
access is disabled, and app navigation is limited to the bundled home screen.
The app shell loads offline and provides a connection/retry banner. Back follows
in-app history. Rotation and fold changes retain the current WebView.

Native background push, closed-app alerts and background GPS are not implemented
in this beta. The rain-alert area says so; the river-alert toggle refers only to
foreground alerts. The original website and backend are unchanged.

## Build

Requires JDK 17, Gradle 8.11.1 and Android SDK 35/build-tools 35.0.0.
Open this directory in Android Studio, or run:

```sh
gradle --no-daemon :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
```

Gradle automatically copies adjacent `floodsafe-nepal/` and `data/` into
generated APK assets before every build. It applies only the Android rain-push
availability copy. Do not edit generated assets directly.

The separate GitHub build workflow builds, checks the APK signature and runs an
Android 15 emulator smoke test with Wi-Fi/mobile data off. It tests the bundled
home, module loading, map open/close, language switch, no startup GPS permission,
and rejection of foreign-origin GPS requests. The inherited 38 web regression
tests cover data freshness/last-good retention and GPS logic. Emulator tests do
not prove physical-device GPS accuracy, live map performance or push delivery.

This APK is debug signed for direct testing, not a Play Store release. The app ID
is `io.github.pujan1234hub.floodsafe.app`, separate from the old browser launcher.
A later build signed with a different debug key may require reinstalling this
beta; uninstalling removes its saved monitoring location/settings. A persistent
production signing identity has not been set up.
