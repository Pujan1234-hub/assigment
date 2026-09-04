from pathlib import Path
import re

root = Path("datemate-android-fixed")
main_path = root / "app/src/main/java/com/pujan/datemate/MainActivity.kt"
gradle_path = root / "app/build.gradle.kts"
manifest_path = root / "app/src/main/AndroidManifest.xml"

text = main_path.read_text(encoding="utf-8")

if "import android.app.Activity\n" not in text:
    text = text.replace(
        "import android.Manifest\n",
        "import android.Manifest\nimport android.app.Activity\n"
    )

start = text.index("    val textRecognizer = remember {")
end = text.index("    fun startSmartScan() {", start)

replacement = r"""    val barcodeScanner = remember {
        val options = GmsBarcodeScannerOptions.Builder()
            .enableAutoZoom()
            .build()

        GmsBarcodeScanning.getClient(context, options)
    }

    val expiryCameraLauncher =
        rememberLauncherForActivityResult(
            contract = ActivityResultContracts.StartActivityForResult()
        ) { result ->

            if (result.resultCode != Activity.RESULT_OK) {
                scanning = false
                scanStage = ""

                val message =
                    result.data
                        ?.getStringExtra(ExpiryCameraActivity.EXTRA_ERROR)
                        .orEmpty()

                if (message.isNotBlank()) {
                    Toast.makeText(
                        context,
                        message,
                        Toast.LENGTH_LONG
                    ).show()
                }

                return@rememberLauncherForActivityResult
            }

            val ocrText =
                result.data
                    ?.getStringExtra(ExpiryCameraActivity.EXTRA_OCR_TEXT)
                    .orEmpty()

            val detectedIso =
                findExpiryDate(ocrText)

            pendingExpiry =
                detectedIso
                    ?.let { isoToInputDate(it) }
                    .orEmpty()

            if (pendingName.isBlank() && ocrText.isNotBlank()) {
                pendingName =
                    guessProductNameFromOcr(
                        ocrText
                    )
            }

            scanning = false
            scanStage = ""
            showAddDialog = true

            if (detectedIso != null) {
                Toast.makeText(
                    context,
                    "Expiry date detected: ${formatIsoDate(detectedIso)}",
                    Toast.LENGTH_SHORT
                ).show()
            } else {
                Toast.makeText(
                    context,
                    "I could not detect the expiry date. You can edit it before saving.",
                    Toast.LENGTH_LONG
                ).show()
            }
        }

    fun openExpiryCamera() {
        scanStage = "Scan the expiry date..."

        try {
            expiryCameraLauncher.launch(
                Intent(
                    context,
                    ExpiryCameraActivity::class.java
                )
            )
        } catch (_: Exception) {
            scanning = false
            scanStage = ""
            showAddDialog = true

            Toast.makeText(
                context,
                "The expiry-date camera could not open. You can enter the date manually.",
                Toast.LENGTH_LONG
            ).show()
        }
    }

"""

text = text[:start] + replacement + text[end:]

for imp in [
    "import android.content.ContentValues\n",
    "import android.graphics.Bitmap\n",
    "import android.os.Handler\n",
    "import android.os.Looper\n",
    "import android.provider.MediaStore\n",
    "import com.google.mlkit.vision.common.InputImage\n",
    "import com.google.mlkit.vision.text.TextRecognition\n",
    "import com.google.mlkit.vision.text.latin.TextRecognizerOptions\n",
]:
    text = text.replace(imp, "")

text = re.sub(
    r'\nfun createTemporaryImageUri\(\n    context: Context\n\): Uri\? \{.*?\n\}\n\nfun deleteTemporaryImageUri\(\n    context: Context,\n    uri: Uri\n\) \{.*?\n\}\n',
    '\n',
    text,
    flags=re.S
)

main_path.write_text(text, encoding="utf-8")

g = gradle_path.read_text(encoding="utf-8")
g = g.replace("versionCode = 2", "versionCode = 3")
g = g.replace('versionName = "1.0.1"', 'versionName = "1.0.2"')

camera_deps = """
    implementation("androidx.camera:camera-core:1.4.1")
    implementation("androidx.camera:camera-camera2:1.4.1")
    implementation("androidx.camera:camera-lifecycle:1.4.1")
    implementation("androidx.camera:camera-view:1.4.1")
"""

if 'androidx.camera:camera-core' not in g:
    g = g.replace(
        '    implementation("androidx.activity:activity-compose:1.10.0")\n',
        '    implementation("androidx.activity:activity-compose:1.10.0")\n' + camera_deps
    )

gradle_path.write_text(g, encoding="utf-8")

m = manifest_path.read_text(encoding="utf-8")

if '<uses-permission android:name="android.permission.CAMERA" />' not in m:
    m = m.replace(
        '<uses-permission android:name="android.permission.INTERNET" />',
        '<uses-permission android:name="android.permission.INTERNET" />\n'
        '    <uses-permission android:name="android.permission.CAMERA" />'
    )

activity_decl = """
        <activity
            android:name=".ExpiryCameraActivity"
            android:exported="false" />
"""

if '.ExpiryCameraActivity' not in m:
    m = m.replace(
        '        <activity\n            android:name=".MainActivity"',
        activity_decl + '\n        <activity\n            android:name=".MainActivity"'
    )

manifest_path.write_text(m, encoding="utf-8")

print("Patched MainActivity, Gradle, and Manifest for CameraX in-app expiry capture.")
