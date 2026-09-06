package np.sathi.ai
import android.app.*
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.speech.*
import androidx.core.app.NotificationCompat
class VoiceWakeService:Service(){ private var recognizer:SpeechRecognizer?=null; private lateinit var speech:NepaliSpeech; private var command=false
 override fun onCreate(){super.onCreate();speech=NepaliSpeech(this);channel();startForeground(77,NotificationCompat.Builder(this,"sathi-listen").setContentTitle("SATHI AI सक्रिय छ").setContentText("‘साथी’ भन्नुहोस्। नेपाली आवाज सुन्दैछ।").setSmallIcon(R.drawable.ic_sathi).setOngoing(true).build());listen()}
 private fun listen(){ if(!SpeechRecognizer.isRecognitionAvailable(this))return; recognizer?.destroy(); recognizer=SpeechRecognizer.createSpeechRecognizer(this).also{r->r.setRecognitionListener(object:RecognitionListener{override fun onResults(b:android.os.Bundle?){val h=b?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull().orEmpty();if(command){command=false;speech.speakNepali(CommandRouter.handle(this@VoiceWakeService,h))}else if(h.contains("साथी",true)||h.contains("sathi",true)){command=true;speech.speakNepali("हजुर, भन्नुहोस्।")};again()} override fun onError(e:Int){again()} override fun onReadyForSpeech(p:android.os.Bundle?){} override fun onBeginningOfSpeech(){} override fun onRmsChanged(v:Float){} override fun onBufferReceived(b:ByteArray?){} override fun onEndOfSpeech(){} override fun onPartialResults(p:android.os.Bundle?){} override fun onEvent(t:Int,p:android.os.Bundle?){} });val i=Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply{putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);putExtra(RecognizerIntent.EXTRA_LANGUAGE,"ne-NP");putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE,"ne-NP");putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE,true)};r.startListening(i)}}
 private fun again(){android.os.Handler(mainLooper).postDelayed({listen()},650)}
 private fun channel(){if(Build.VERSION.SDK_INT>=26)getSystemService(NotificationManager::class.java).createNotificationChannel(NotificationChannel("sathi-listen","SATHI AI पृष्ठभूमि आवाज",NotificationManager.IMPORTANCE_LOW))}
 override fun onDestroy(){recognizer?.destroy();speech.close();super.onDestroy()} override fun onBind(i:Intent?):IBinder?=null
}
