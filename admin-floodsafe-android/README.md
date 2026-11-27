# Admin FloodSafe v1.1.0

Separate Android owner console with both safe content OTA and **non-emergency Firebase Push** workflows.

## Features

- Create and publish bilingual in-app OTA message, set duration up to 14 days
- Remove existing in-app OTA message
- Verify live OTA revision after GitHub workflow dispatch (not just queued)
- Push notification to Play-installed subscribers via FCM topic `nepal-alerts`
- Preview-only push for `.preview` builds via `floodsafe-testers`
- Push history and OTA workflow history with success/failure status
- Mandatory Android confirmation dialog before push to subscribers
- GitHub fine-grained token, Keystore-encrypted locally; never built into APK

## How to connect

Create a fine-grained GitHub PAT using https://github.com/settings/personal-access-tokens/new:
- owner Pujan1234-hub
- only repository `assigment`
- Actions: Read and write
- Metadata: Read (automatic)
- short expiration

Paste it in the Admin FloodSafe connect screen. Never share the token in chat or screenshots.

## Important: removal latency in original Play beta

The existing FloodSafe Nepal **v0.9.23** fetches content config on an approximately 5-minute timer. Disabling a message in the admin app updates the server, but the text on **already open** v0.9.23 cannot be erased instantaneously by an external app. Its cache remains until the next successful poll. This requires a separate Play beta update to reduce/remove client-side latency. Admin v1.1 explicitly differentiates GitHub queued from confirmed server removal. Notifications already delivered to the Android status bar cannot be recalled.

## Target audience and safety

The release version of FloodSafe Nepal subscribes to `nepal-alerts`, **not** `floodsafe-testers`. Although the app is currently in closed beta, `nepal-alerts` may also include older installers. Therefore sender confirmation is mandatory; use only general non-emergency notices. The distinct preview topic reaches `.preview` builds only.
No river danger threshold, BIPAD/DHM official warning, GPS risk logic, permissions, or credentials are modified.

## Android package/signing

Application ID `com.pjbuilts.adminfloodsafe.v11` is new and installs side-by-side with v1.0.0. We cannot reuse v1.0.0's ephemeral signing key, so it cannot update that APK directly. Please do not uninstall the old app before verifying your new GitHub token connection; previous encrypted tokens cannot be transferred or recovered from AndroidKeyStore.

Separate APK, independent from public FloodSafe Nepal v0.9.23. No Firebase service account embedded in the APK; GitHub Actions uses configured secret in its secure runner.

## v1.2.0 — one-device notification test

The new **Test on my phone only** button sends a fixed, clearly labelled informational test via the existing GitHub workflow. The `device` audience targets only the exact registration token in the private repository Actions secret `FLOODSAFE_OWNER_TEST_FCM_TOKEN`. It never uses a topic or falls back to a broadcast. A missing/invalid secret stops before Firebase authentication. No token is included in the app or logged. Firebase accepts a request, but this is not proof of handset delivery. The current public v1.0.0 has no owner-token export/pairing UI; a valid registration token must be provisioned privately before this feature can deliver. This is a new side-by-side admin package (`com.pjbuilts.adminfloodsafe.v12`) because the previous ephemeral signing key is unavailable. Keep the old admin installed until the new one is connected. Do not paste FCM tokens into chat or dispatch inputs. No changes to public Android app or website.
