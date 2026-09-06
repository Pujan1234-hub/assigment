package np.sathi.ai
import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.*
import android.provider.Settings
import android.speech.*
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
class MainActivity:AppCompatActivity(){private lateinit var speech:NepaliSpeech;private lateinit var status:TextView;private var rec:SpeechRecognizer?=null
 override fun onCreate(b:Bundle?){super.onCreate(b);setContentView(R.layout.activity_main);speech=NepaliSpeech(this);status=findViewById(R.id.status);requestBasics();findViewById<Button>(R.id.talkButton).setOnClickListener{listenOnce()};findViewById<Button>(R.id.backgroundButton).setOnClickListener{if(ContextCompat.checkSelfPermission(this,Manifest.permission.RECORD_AUDIO)==PackageManager.PERMISSION_GRANTED){ContextCompat.startForegroundService(this,Intent(this,VoiceWakeService::class.java));status.text="पृष्ठभूमिमा सक्रिय — ‘साथी’ भन्नुहोस्"}else requestBasics()};findViewById<Button>(R.id.askButton).setOnClickListener{val q=findViewById<EditText>(R.id.question).text.toString();val a=CommandRouter.handle(this,q);status.text=a;speech.speakNepali(a)};findViewById<Button>(R.id.studyButton).setOnClickListener{startActivity(Intent(this,StudyActivity::class.java))};findViewById<Button>(R.id.notificationButton).setOnClickListener{startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))}}
 private fun requestBasics(){val p=mutableListOf(Manifest.permission.RECORD_AUDIO);if(Build.VERSION.SDK_INT>=33)p+=Manifest.permission.POST_NOTIFICATIONS;ActivityCompat.requestPermissions(this,p.toTypedArray(),400)}
 private fun listenOnce(){if(!SpeechRecognizer.isRecognitionAvailable(this)){status.text="आवाज पहिचान सेवा उपलब्ध छैन।";return};rec?.destroy();rec=SpeechRecognizer.createSpeechRecognizer(this);rec?.setRecognitionListener(object:RecognitionListener{override fun onResults(b:Bundle?){val h=b?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull().orEmpty();val a=CommandRouter.handle(this@MainActivity,h);status.text=a;speech.speakNepali(a)}override fun onError(e:Int){status.text="फेरि भन्नुहोस्।"}override fun onReadyForSpeech(p:Bundle?){status.text="सुन्दैछु…"}override fun onBeginningOfSpeech(){}override fun onRmsChanged(v:Float){}override fun onBufferReceived(b:ByteArray?){}override fun onEndOfSpeech(){}override fun onPartialResults(p:Bundle?){}override fun onEvent(t:Int,p:Bundle?){}});val i=Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply{putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);putExtra(RecognizerIntent.EXTRA_LANGUAGE,"ne-NP");putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE,"ne-NP");putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE,true)};rec?.startListening(i)}
 override fun onDestroy(){rec?.destroy();speech.close();super.onDestroy()}}
