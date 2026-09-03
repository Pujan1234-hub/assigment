# FloodSafe Nepal — iPhone/iPad build (Mac required)

This folder turns the existing FloodSafe Nepal interface into a native iOS app shell using Capacitor. It must be built on a Mac using Xcode; Windows cannot create a signed iPhone install.

## Send this whole source ZIP to the Mac

Download the repository ZIP from the GitHub **main** branch, extract it, then open Terminal inside the `ios-app` folder.

## Requirements on the Mac

1. macOS with the newest Xcode supported by that Mac (install from the Mac App Store).
2. Open Xcode once and accept its licence / install components.
3. Node.js 20 or newer (install from https://nodejs.org).
4. An Apple ID for device testing.
5. For TestFlight / sharing outside the Mac owner's own phone: Apple Developer Program membership is required.
6. Internet connection while building, because npm downloads the Capacitor packages.

## First build commands

```bash
cd ios-app
npm install
npm run ios:add
npm run ios:open
```

This creates `ios/App` and opens the Xcode project. For every later source change:

```bash
npm run ios:sync
npm run ios:open
```

## In Xcode

1. Select **App** in the left project panel.
2. Under **Signing & Capabilities**, select the friend's Team.
3. Set a unique Bundle Identifier, for example `com.pujanchapagain.floodsafenepal`.
4. Connect an iPhone, select it at the top, and press ▶ Run.

For a shareable beta: Xcode → Product → Archive → Distribute App → TestFlight/App Store Connect.

## Required iPhone permissions

After `ios:add`, edit `ios/App/App/Info.plist` and add these keys inside the main `<dict>`:

```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>FloodSafe Nepal uses your location to show local weather and nearby flood information.</string>
<key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
<string>FloodSafe Nepal uses location while you use the app to show local weather and nearby flood information.</string>
```

This is needed before location works on an iPhone.

## Push notifications

The included Android `google-services.json` does **not** configure iOS.

To enable real iPhone push notifications, the friend must:
1. Add an iOS app with the same Bundle Identifier in Firebase.
2. Download `GoogleService-Info.plist` and add it to the Xcode **App** target.
3. In Apple Developer Certificates/Identifiers, enable **Push Notifications** for that identifier.
4. Create/upload an APNs key to Firebase Cloud Messaging.
5. Add iOS FCM native code/capability. Until this is completed, river/weather viewing works but background push alerts are not enabled.

Do not claim automatic emergency alerts are active until a real Firebase/APNs test notification arrives on an iPhone.

## Test checklist

- App opens without a blank page.
- Tap current location → iPhone permission prompt appears → weather updates.
- River map, official river data and news load over Wi-Fi and mobile data.
- Nepali/English button works.
- TestFlight build installs on a second iPhone.
