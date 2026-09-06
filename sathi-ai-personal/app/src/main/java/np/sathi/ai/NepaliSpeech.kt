package np.sathi.ai
import android.content.Context
import android.speech.tts.TextToSpeech
import java.util.Locale
class NepaliSpeech(context: Context): TextToSpeech.OnInitListener {
 private val tts=TextToSpeech(context.applicationContext,this); private var ready=false
 override fun onInit(status:Int){ if(status==TextToSpeech.SUCCESS){ val result=tts.setLanguage(Locale("ne","NP")); ready=result!=TextToSpeech.LANG_MISSING_DATA && result!=TextToSpeech.LANG_NOT_SUPPORTED; tts.setSpeechRate(0.96f)}}
 fun speakNepali(text:String){ if(ready) tts.speak(text,TextToSpeech.QUEUE_FLUSH,null,"sathi-nepali") }
 fun close(){tts.stop();tts.shutdown()}
}
