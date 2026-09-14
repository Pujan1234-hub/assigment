package com.pujan.datemate

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.os.SystemClock
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ExperimentalGetImage
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import java.io.File
import java.util.Calendar
import java.util.GregorianCalendar
import java.util.Locale
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

class ExpiryCameraActivity : ComponentActivity() {

    companion object {
        const val EXTRA_OCR_TEXT = "datemate_ocr_text"
        const val EXTRA_EXPIRY_ISO = "datemate_expiry_iso"
        const val EXTRA_ERROR = "datemate_camera_error"
    }

    private lateinit var previewView: PreviewView
    private lateinit var captureButton: Button
    private lateinit var cancelButton: Button
    private lateinit var statusText: TextView
    private lateinit var progressBar: ProgressBar
    private lateinit var cameraExecutor: ExecutorService

    private var imageCapture: ImageCapture? = null
    private var analysis: ImageAnalysis? = null
    private var lastAnalysisAt = 0L
    private var lastCandidate: String? = null
    private var candidateHits = 0

    private val analysisBusy = AtomicBoolean(false)
    private val resultDelivered = AtomicBoolean(false)

    private val recognizer by lazy {
        TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
    }

    private val permissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) {
                startCamera()
            } else {
                finishWithError("Camera permission is required to scan the expiry date.")
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        cameraExecutor = Executors.newSingleThreadExecutor()
        buildUi()

        if (
            ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) ==
            PackageManager.PERMISSION_GRANTED
        ) {
            startCamera()
        } else {
            permissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    override fun onDestroy() {
        try {
            analysis?.clearAnalyzer()
        } catch (_: Exception) {
        }

        try {
            recognizer.close()
        } catch (_: Exception) {
        }

        if (::cameraExecutor.isInitialized) {
            cameraExecutor.shutdown()
        }

        super.onDestroy()
    }

    private fun buildUi() {
        val root = FrameLayout(this).apply {
            setBackgroundColor(Color.BLACK)
        }

        previewView = PreviewView(this).apply {
            implementationMode = PreviewView.ImplementationMode.COMPATIBLE
        }

        root.addView(
            previewView,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
            )
        )

        val instruction = TextView(this).apply {
            text = "Auto expiry scan\nPoint the camera at SEP 5, 5 SEP, USE BY, BEST BEFORE or EXP"
            setTextColor(Color.WHITE)
            textSize = 17f
            gravity = Gravity.CENTER
            setPadding(18.dp, 16.dp, 18.dp, 16.dp)
            setBackgroundColor(0x99000000.toInt())
        }

        root.addView(
            instruction,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.WRAP_CONTENT,
                Gravity.TOP
            )
        )

        val guide = View(this).apply {
            background = android.graphics.drawable.GradientDrawable().apply {
                setColor(0x1200C9C8)
                setStroke(3.dp, 0xFF00D1CE.toInt())
                cornerRadius = 18.dp.toFloat()
            }
        }

        root.addView(
            guide,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                150.dp,
                Gravity.CENTER
            ).apply {
                leftMargin = 24.dp
                rightMargin = 24.dp
            }
        )

        val middle = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
        }

        progressBar = ProgressBar(this).apply {
            visibility = View.GONE
        }

        statusText = TextView(this).apply {
            text = "Starting camera..."
            setTextColor(Color.WHITE)
            textSize = 15f
            gravity = Gravity.CENTER
            setPadding(14.dp, 10.dp, 14.dp, 10.dp)
            setBackgroundColor(0x99000000.toInt())
        }

        middle.addView(progressBar)
        middle.addView(statusText)

        root.addView(
            middle,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.WRAP_CONTENT,
                FrameLayout.LayoutParams.WRAP_CONTENT,
                Gravity.CENTER
            )
        )

        val controls = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
            setPadding(16.dp, 14.dp, 16.dp, 20.dp)
            setBackgroundColor(0x99000000.toInt())
        }

        cancelButton = Button(this).apply {
            text = "Cancel"
            setOnClickListener {
                setResult(Activity.RESULT_CANCELED)
                finish()
            }
        }

        captureButton = Button(this).apply {
            text = "CAPTURE IF NEEDED"
            isEnabled = false
            setOnClickListener {
                capturePhoto()
            }
        }

        controls.addView(
            cancelButton,
            LinearLayout.LayoutParams(0, 56.dp, 1f).apply {
                marginEnd = 8.dp
            }
        )

        controls.addView(
            captureButton,
            LinearLayout.LayoutParams(0, 56.dp, 1.4f).apply {
                marginStart = 8.dp
            }
        )

        root.addView(
            controls,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.WRAP_CONTENT,
                Gravity.BOTTOM
            )
        )

        setContentView(root)
    }

    private fun startCamera() {
        setBusy("Starting camera...")

        val future = ProcessCameraProvider.getInstance(this)

        future.addListener({
            try {
                val provider = future.get()

                val preview = Preview.Builder().build().also {
                    it.setSurfaceProvider(previewView.surfaceProvider)
                }

                imageCapture = ImageCapture.Builder()
                    .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
                    .setJpegQuality(92)
                    .build()

                analysis = ImageAnalysis.Builder()
                    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                    .build()
                    .also { imageAnalysis ->
                        imageAnalysis.setAnalyzer(cameraExecutor) { proxy ->
                            analyzeFrame(proxy)
                        }
                    }

                provider.unbindAll()

                provider.bindToLifecycle(
                    this,
                    CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,
                    imageCapture,
                    analysis
                )

                runOnUiThread {
                    progressBar.visibility = View.GONE
                    statusText.text = "Scanning automatically • hold the date steady"
                    captureButton.isEnabled = true
                    cancelButton.isEnabled = true
                }

            } catch (_: Exception) {
                finishWithError("DateMate could not start the camera. Please try again.")
            }
        }, ContextCompat.getMainExecutor(this))
    }

    @OptIn(ExperimentalGetImage::class)
    private fun analyzeFrame(proxy: ImageProxy) {
        if (resultDelivered.get()) {
            proxy.close()
            return
        }

        val now = SystemClock.elapsedRealtime()

        if (now - lastAnalysisAt < 350L || !analysisBusy.compareAndSet(false, true)) {
            proxy.close()
            return
        }

        lastAnalysisAt = now

        val mediaImage = proxy.image

        if (mediaImage == null) {
            analysisBusy.set(false)
            proxy.close()
            return
        }

        val input = InputImage.fromMediaImage(
            mediaImage,
            proxy.imageInfo.rotationDegrees
        )

        recognizer.process(input)
            .addOnSuccessListener { result ->
                val text = result.text
                val iso = detectExpiryIso(text)

                if (iso != null) {
                    if (iso == lastCandidate) {
                        candidateHits += 1
                    } else {
                        lastCandidate = iso
                        candidateHits = 1
                    }

                    runOnUiThread {
                        statusText.text =
                            "Detected ${displayIso(iso)} • hold steady ${candidateHits}/2"
                    }

                    if (candidateHits >= 2) {
                        deliverResult(text, iso)
                    }
                } else {
                    lastCandidate = null
                    candidateHits = 0
                }
            }
            .addOnCompleteListener {
                analysisBusy.set(false)
                proxy.close()
            }
    }

    private fun capturePhoto() {
        val capture = imageCapture ?: return

        setBusy("Capturing photo...")

        val file = File.createTempFile(
            "datemate_expiry_",
            ".jpg",
            cacheDir
        )

        val options = ImageCapture.OutputFileOptions.Builder(file).build()

        capture.takePicture(
            options,
            cameraExecutor,
            object : ImageCapture.OnImageSavedCallback {
                override fun onImageSaved(
                    outputFileResults: ImageCapture.OutputFileResults
                ) {
                    runOnUiThread {
                        statusText.text = "Reading expiry date..."
                    }

                    runFullPhotoOcr(file)
                }

                override fun onError(exception: ImageCaptureException) {
                    file.delete()

                    runOnUiThread {
                        progressBar.visibility = View.GONE
                        statusText.text = "Capture failed • try again"
                        captureButton.isEnabled = true
                        cancelButton.isEnabled = true
                    }
                }
            }
        )
    }

    private fun runFullPhotoOcr(file: File) {
        cameraExecutor.execute {
            try {
                val image = InputImage.fromFilePath(
                    applicationContext,
                    Uri.fromFile(file)
                )

                recognizer.process(image)
                    .addOnSuccessListener { result ->
                        file.delete()

                        val iso = detectExpiryIso(result.text)

                        if (iso != null) {
                            deliverResult(result.text, iso)
                        } else {
                            if (resultDelivered.compareAndSet(false, true)) {
                                setResult(
                                    Activity.RESULT_OK,
                                    Intent().putExtra(EXTRA_OCR_TEXT, result.text)
                                )
                                finish()
                            }
                        }
                    }
                    .addOnFailureListener {
                        file.delete()

                        runOnUiThread {
                            progressBar.visibility = View.GONE
                            statusText.text = "Could not read text • try again"
                            captureButton.isEnabled = true
                            cancelButton.isEnabled = true
                        }
                    }

            } catch (_: Exception) {
                file.delete()

                runOnUiThread {
                    progressBar.visibility = View.GONE
                    statusText.text = "Could not prepare photo • try again"
                    captureButton.isEnabled = true
                    cancelButton.isEnabled = true
                }
            }
        }
    }

    private fun deliverResult(text: String, iso: String) {
        if (!resultDelivered.compareAndSet(false, true)) {
            return
        }

        runOnUiThread {
            setResult(
                Activity.RESULT_OK,
                Intent()
                    .putExtra(EXTRA_OCR_TEXT, text)
                    .putExtra(EXTRA_EXPIRY_ISO, iso)
            )

            finish()
        }
    }

    private fun detectExpiryIso(raw: String): String? {
        if (raw.isBlank()) {
            return null
        }

        val text = normalizeOcr(raw)
        val month =
            "(?:JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUN(?:E)?|JUL(?:Y)?|AUG(?:UST)?|SEP(?:T|TEMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)"

        val priorityZones = mutableListOf<String>()
        val keywordRegex = Regex(
            """\b(?:USE\s*BY|USE\s*BEFORE|BEST\s*BEFORE|BEST\s*BY|BBE|BBD|EXPIRY|EXPIRATION|EXPIRES|EXP\.?|BB)\b"""
        )

        keywordRegex.findAll(text).forEach { match ->
            val start = match.range.first
            val end = minOf(text.length, start + 100)
            priorityZones.add(text.substring(start, end))
        }

        priorityZones.forEach { zone ->
            parseExpiryZone(zone, month)?.let {
                return it
            }
        }

        return parseExpiryZone(text, month)
    }

    private fun parseExpiryZone(text: String, monthWord: String): String? {
        Regex(
            """\b(20\d{2})[/\.\-\s](0?[1-9]|1[0-2])[/\.\-\s](0?[1-9]|[12]\d|3[01])\b"""
        ).find(text)?.let {
            return validIso(
                it.groupValues[1].toInt(),
                it.groupValues[2].toInt(),
                it.groupValues[3].toInt()
            )
        }

        Regex(
            """\b(0?[1-9]|[12]\d|3[01])[/\.\-\s](0?[1-9]|1[0-2])[/\.\-\s](20\d{2}|\d{2})\b"""
        ).find(text)?.let {
            return validIso(
                normalizeYear(it.groupValues[3].toInt()),
                it.groupValues[2].toInt(),
                it.groupValues[1].toInt()
            )
        }

        Regex(
            """\b($monthWord)[\s\.\-_/]*(0?[1-9]|[12]\d|3[01])(?:ST|ND|RD|TH)?(?:[\s,\.\-_/]+(20\d{2}|\d{2}))?\b"""
        ).find(text)?.let {
            val month = monthNumber(it.groupValues[1])
            val day = it.groupValues[2].toInt()
            val yearText = it.groupValues.getOrNull(3).orEmpty()

            return if (yearText.isBlank()) {
                nearestFutureIso(month, day)
            } else {
                validIso(normalizeYear(yearText.toInt()), month, day)
            }
        }

        Regex(
            """\b(0?[1-9]|[12]\d|3[01])(?:ST|ND|RD|TH)?[\s\.\-_/]*($monthWord)(?:[\s,\.\-_/]+(20\d{2}|\d{2}))?\b"""
        ).find(text)?.let {
            val day = it.groupValues[1].toInt()
            val month = monthNumber(it.groupValues[2])
            val yearText = it.groupValues.getOrNull(3).orEmpty()

            return if (yearText.isBlank()) {
                nearestFutureIso(month, day)
            } else {
                validIso(normalizeYear(yearText.toInt()), month, day)
            }
        }

        Regex(
            """\b(0?[1-9]|1[0-2])[/\.\-](20\d{2}|\d{2})\b"""
        ).find(text)?.let {
            val month = it.groupValues[1].toInt()
            val year = normalizeYear(it.groupValues[2].toInt())
            return lastDayIso(year, month)
        }

        Regex(
            """\b($monthWord)[\s\.\-_/]*(20\d{2}|\d{2})\b"""
        ).find(text)?.let {
            val month = monthNumber(it.groupValues[1])
            val year = normalizeYear(it.groupValues[2].toInt())
            return lastDayIso(year, month)
        }

        return null
    }

    private fun normalizeOcr(raw: String): String {
        return raw
            .uppercase(Locale.UK)
            .replace('’', '\'')
            .replace('–', '-')
            .replace('—', '-')
            .replace(Regex("""\s+"""), " ")
            .replace("SEPT.", "SEP")
            .replace("SEPT ", "SEP ")
            .trim()
    }

    private fun normalizeYear(year: Int): Int {
        return if (year < 100) {
            2000 + year
        } else {
            year
        }
    }

    private fun nearestFutureIso(month: Int, day: Int): String? {
        val now = Calendar.getInstance()
        var year = now.get(Calendar.YEAR)

        var iso = validIso(year, month, day) ?: return null

        val today = GregorianCalendar(
            now.get(Calendar.YEAR),
            now.get(Calendar.MONTH),
            now.get(Calendar.DAY_OF_MONTH)
        )

        val parts = iso.split("-")
        val candidate = GregorianCalendar(
            parts[0].toInt(),
            parts[1].toInt() - 1,
            parts[2].toInt()
        )

        if (candidate.before(today)) {
            year += 1
            iso = validIso(year, month, day) ?: return null
        }

        return iso
    }

    private fun lastDayIso(year: Int, month: Int): String? {
        if (month !in 1..12) {
            return null
        }

        return try {
            val calendar = GregorianCalendar(year, month - 1, 1)
            calendar.isLenient = false

            validIso(
                year,
                month,
                calendar.getActualMaximum(Calendar.DAY_OF_MONTH)
            )
        } catch (_: Exception) {
            null
        }
    }

    private fun validIso(year: Int, month: Int, day: Int): String? {
        if (year !in 2000..2099 || month !in 1..12 || day !in 1..31) {
            return null
        }

        return try {
            val calendar = GregorianCalendar()
            calendar.isLenient = false
            calendar.clear()
            calendar.set(year, month - 1, day, 12, 0, 0)
            calendar.time

            "%04d-%02d-%02d".format(
                Locale.UK,
                year,
                month,
                day
            )
        } catch (_: Exception) {
            null
        }
    }

    private fun monthNumber(text: String): Int {
        return when (text.take(3)) {
            "JAN" -> 1
            "FEB" -> 2
            "MAR" -> 3
            "APR" -> 4
            "MAY" -> 5
            "JUN" -> 6
            "JUL" -> 7
            "AUG" -> 8
            "SEP" -> 9
            "OCT" -> 10
            "NOV" -> 11
            "DEC" -> 12
            else -> 0
        }
    }

    private fun displayIso(iso: String): String {
        val p = iso.split("-")

        if (p.size != 3) {
            return iso
        }

        val month = when (p[1]) {
            "01" -> "Jan"
            "02" -> "Feb"
            "03" -> "Mar"
            "04" -> "Apr"
            "05" -> "May"
            "06" -> "Jun"
            "07" -> "Jul"
            "08" -> "Aug"
            "09" -> "Sep"
            "10" -> "Oct"
            "11" -> "Nov"
            "12" -> "Dec"
            else -> p[1]
        }

        return "${p[2].toIntOrNull() ?: p[2]} $month ${p[0]}"
    }

    private fun setBusy(message: String) {
        runOnUiThread {
            progressBar.visibility = View.VISIBLE
            statusText.text = message
            captureButton.isEnabled = false
            cancelButton.isEnabled = false
        }
    }

    private fun finishWithError(message: String) {
        setResult(
            Activity.RESULT_CANCELED,
            Intent().putExtra(EXTRA_ERROR, message)
        )
        finish()
    }

    private val Int.dp: Int
        get() = (this * resources.displayMetrics.density).toInt()
}
