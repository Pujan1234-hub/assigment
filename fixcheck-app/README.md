# FixCheck App

Cross-platform packaging for FixCheck.

## Targets
- Android: Capacitor APK/AAB
- iOS/iPadOS: Capacitor Xcode project. A physical-device/App Store IPA requires Apple signing.
- Windows: Electron portable app
- macOS: Electron app ZIP. CI build is unsigned until Apple signing/notarisation is configured.

## Measurement integrity
The packaged UI is bundled locally so it can open offline. The FixCheck comparison baseline points to the live HTTPS endpoint `https://pujan1234-hub.github.io/assigment/ping.txt`; it does not benchmark a bundled local file.

## Development
Run `npm install`, then `npx cap add android` / `npx cap add ios` for mobile or `npm run desktop:start` for desktop.
