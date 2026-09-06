package np.sathi.ai
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.provider.Settings
import java.util.Locale
object CommandRouter {
 fun handle(context:Context,raw:String):String { val q=raw.trim(); val lower=q.lowercase(); return when {
  lower.contains("क्यामेरा") -> {context.startActivity(Intent("android.media.action.IMAGE_CAPTURE").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));"क्यामेरा खोल्दैछु।"}
  lower.contains("सेटिङ") -> {context.startActivity(Intent(Settings.ACTION_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));"फोनको सेटिङ खोल्दैछु।"}
  lower.contains("नक्सा")||lower.contains("म्याप") -> {context.startActivity(Intent(Intent.ACTION_VIEW,Uri.parse("geo:0,0?q="+Uri.encode(q))).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));"नक्सामा खोज्दैछु।"}
  lower.startsWith("खोज")||lower.contains("वेबमा")||lower.contains("गुगल") -> {context.startActivity(Intent(Intent.ACTION_VIEW,Uri.parse("https://www.google.com/search?q="+Uri.encode(q))).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));"वेबमा खोज्दैछु।"}
  lower.contains("समय") -> {val now=java.text.SimpleDateFormat("h:mm",Locale("ne","NP")).format(java.util.Date());"अहिले $now बजेको छ।"}
  else -> "यो कुरा बुझें। पूर्ण AI उत्तर प्रणाली अर्को तहमा जोडिँदैछ। अहिले म फोनका आधारभूत काम र वेब खोज गर्न सक्छु।"
 }}
}
