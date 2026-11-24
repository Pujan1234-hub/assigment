# Admin FloodSafe v1.0.0
Independent Android app for Pujan's existing FloodSafe Nepal **in-app OTA notices**.

The app sends GitHub Actions workflow-dispatch requests, not notifications directly:
- Existing workflow: .github/workflows/floodsafe-ota-message-admin.yml on main.
- Existing config: floodsafe-ota-config-v0921/ota/floodsafe-config-v1.json.
- River alert logic, Firebase push and Play Store APK are untouched.

## Setup (once)
Create a GitHub **fine-grained personal access token** at https://github.com/settings/personal-access-tokens/new:
- Resource owner: Pujan1234-hub
- Repository access: Only select repository, assigment
- Repository permissions: Actions = Read and write; Metadata = Read (automatic)
- Choose a short expiry and renew as needed.
- No Contents write, no classic full-scope PAT, no Firebase key, no repository secrets in APK.

Open Admin FloodSafe, paste the token in the password field, tap Connect.
Token stored encrypted by Android Keystore AES-256 GCM.
You can disconnect and wipe the saved token anytime.

## Function
Type title/body and optional Nepali versions, choose duration 1..336 hours,
Publish, or Remove. Accepted dispatch does NOT mean the job has succeeded:
check workflow history and the Live OTA status in the app.
The live config is polled by FloodSafe Nepal (usually within five minutes).

## Installation
Independent package com.pjbuilts.adminfloodsafe. No Firebase, GPS, contact
permissions or analytics. Does not modify the original FloodSafe APK.
The first release's signing certificate must be retained before issuing upgrades;
this prototype's workflow generates a one-time signing identity, so reinstall
may be necessary for a future different-key release.
