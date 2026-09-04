from pathlib import Path

root = Path("datemate-android-fixed")
main_path = root / "app/src/main/java/com/pujan/datemate/MainActivity.kt"
app_gradle = root / "app/build.gradle.kts"
root_gradle = root / "build.gradle.kts"
manifest = root / "app/src/main/AndroidManifest.xml"

# --- MainActivity: add Privacy Policy entry in Settings ---
text = main_path.read_text(encoding="utf-8")

settings_block = '''        item {\n            OutlinedButton(\n                onClick = { openNotificationSettings(context) },\n                modifier = Modifier.fillMaxWidth()\n            ) {\n                Text(\n                    "Open notification settings",\n                    color = DateMateBlue\n                )\n            }\n        }\n'''

privacy_block = '''        item {\n            OutlinedButton(\n                onClick = { openNotificationSettings(context) },\n                modifier = Modifier.fillMaxWidth()\n            ) {\n                Text(\n                    "Open notification settings",\n                    color = DateMateBlue\n                )\n            }\n        }\n\n        item {\n            OutlinedButton(\n                onClick = { openPrivacyPolicy(context) },\n                modifier = Modifier.fillMaxWidth()\n            ) {\n                Text(\n                    "Privacy Policy",\n                    color = DateMateBlue\n                )\n            }\n        }\n'''

if "openPrivacyPolicy(context)" not in text:
    if settings_block not in text:
        raise RuntimeError("Could not find Settings notification button")
    text = text.replace(settings_block, privacy_block, 1)

if "fun openPrivacyPolicy(context: Context)" not in text:
    text += '''\n\nfun openPrivacyPolicy(context: Context) {\n    val url = Uri.parse(\n        "https://github.com/Pujan1234-hub/assigment/blob/main/DATEMATE_PRIVACY_POLICY.md"\n    )\n\n    context.startActivity(\n        Intent(Intent.ACTION_VIEW, url)\n    )\n}\n'''

main_path.write_text(text, encoding="utf-8")

# --- Google Play 2026 target API requirement ---
g = app_gradle.read_text(encoding="utf-8")
g = g.replace("compileSdk = 35", "compileSdk = 36")
g = g.replace("targetSdk = 35", "targetSdk = 36")
g = g.replace("versionCode = 3", "versionCode = 4")
g = g.replace('versionName = "1.0.2"', 'versionName = "1.0.3"')
app_gradle.write_text(g, encoding="utf-8")

rg = root_gradle.read_text(encoding="utf-8")
rg = rg.replace(
    'id("com.android.application") version "8.7.3" apply false',
    'id("com.android.application") version "8.10.1" apply false'
)
root_gradle.write_text(rg, encoding="utf-8")

# --- Manifest privacy / device compatibility cleanup ---
m = manifest.read_text(encoding="utf-8")
m = m.replace('android:allowBackup="true"', 'android:allowBackup="false"')
m = m.replace(
    'android:name=".BootReceiver"\n            android:enabled="true"\n            android:exported="true"',
    'android:name=".BootReceiver"\n            android:enabled="true"\n            android:exported="false"'
)

if '<uses-feature android:name="android.hardware.camera.any" android:required="false" />' not in m:
    m = m.replace(
        '<uses-permission android:name="android.permission.CAMERA" />',
        '<uses-permission android:name="android.permission.CAMERA" />\n'
        '    <uses-feature android:name="android.hardware.camera.any" android:required="false" />'
    )

manifest.write_text(m, encoding="utf-8")

print("DateMate Play Store patch applied: API 36, v1.0.3, privacy link, manifest hardening.")
