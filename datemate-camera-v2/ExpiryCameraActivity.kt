package com.pujan.datemate

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
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
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import java.io.File
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class ExpiryCameraActivity : ComponentActivity() {

    companion object {
        const val EXTRA_OCR_TEXT = "datemate_ocr_text"
        const val EXTRA_ERROR = "datemate_camera_error"
    }

    private lateinit var previewView: PreviewView
    private lateinit var captureButton: Button
    private lateinit var cancelButton: Button
    private lateinit var statusText: TextView
    private lateinit var progressBar: ProgressBar
    private lateinit var cameraExecutor: ExecutorService
    private var imageCapture: ImageCapture? = null

    private val recognizer by lazy {
        TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
    }

    private val permissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) startCamera()
            else finishWithError("Camera permission is required to scan the expiry date.")
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
        try { recognizer.close() } catch (_: Exception) {}
        if (::cameraExecutor.isInitialized) cameraExecutor.shutdown()
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
            text = "Scan expiry date\nKeep USE BY / BEST BEFORE / EXP clear and fill the frame"
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
            text = "CAPTURE"
            isEnabled = false
            setOnClickListener { capturePhoto() }
        }

        controls.addView(
            cancelButton,
            LinearLayout.LayoutParams(0, 56.dp, 1f).apply {
                marginEnd = 8.dp
            }
        )

        controls.addView(
            captureButton,
            LinearLayout.LayoutParams(0, 56.dp, 1f).apply {
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
                    .setJpegQuality(90)
                    .build()

                provider.unbindAll()

                provider.bindToLifecycle(
                    this,
                    CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,
                    imageCapture
                )

                progressBar.visibility = View.GONE
                statusText.text = "Ready • keep the printed date sharp"
                captureButton.isEnabled = true
                cancelButton.isEnabled = true

            } catch (_: Exception) {
                finishWithError("DateMate could not start the camera. Please try again.")
            }
        }, ContextCompat.getMainExecutor(this))
    }

    private fun capturePhoto() {
        val capture = imageCapture ?: return

        setBusy("Capturing photo...")

        val file = File.createTempFile("datemate_expiry_", ".jpg", cacheDir)
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

                    runOcr(file)
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

    private fun runOcr(file: File) {
        cameraExecutor.execute {
            try {
                val image = InputImage.fromFilePath(
                    applicationContext,
                    Uri.fromFile(file)
                )

                recognizer.process(image)
                    .addOnSuccessListener { result ->
                        file.delete()

                        setResult(
                            Activity.RESULT_OK,
                            Intent().putExtra(EXTRA_OCR_TEXT, result.text)
                        )

                        finish()
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

    private fun setBusy(message: String) {
        progressBar.visibility = View.VISIBLE
        statusText.text = message
        captureButton.isEnabled = false
        cancelButton.isEnabled = false
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
