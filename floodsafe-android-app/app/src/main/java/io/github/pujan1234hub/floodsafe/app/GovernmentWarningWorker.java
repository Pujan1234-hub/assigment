package io.github.pujan1234hub.floodsafe.app;
import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;
import android.net.Uri;
import androidx.annotation.NonNull;
import androidx.work.Worker;
import androidx.work.WorkerParameters;
import org.json.JSONArray;
import org.json.JSONObject;

/** Only sends source-linked government bulletin updates, not fabricated gauge thresholds. */
public final class GovernmentWarningWorker extends Worker {
 public GovernmentWarningWorker(@NonNull Context c,@NonNull WorkerParameters p){super(c,p);}
 @NonNull @Override public Result doWork(){
  Context app=getApplicationContext();
  if(Build.VERSION.SDK_INT>=33&&app.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return Result.success();
  try{
   JSONObject j=GovernmentNotices.fetch();
   JSONArray a=GovernmentNotices.active(j,System.currentTimeMillis());
   SharedPreferences p=app.getSharedPreferences("fs-gov-notices",Context.MODE_PRIVATE);
   StringBuilder keys=new StringBuilder();
   for(int i=0;i<a.length();i++){JSONObject n=a.optJSONObject(i);if(n!=null)keys.append(n.optString("id")).append('|');}
   String now=keys.toString();
   if(now.isEmpty()){
      NotificationManager notifications=(NotificationManager)app.getSystemService(Context.NOTIFICATION_SERVICE);
      if(notifications!=null)notifications.cancel(1402);
      p.edit().putString("latest","").apply();
      return Result.success();
   }
   if(now.equals(p.getString("latest","")))return Result.success();
   JSONObject first=a.optJSONObject(0);if(first==null)return Result.success();
   String link=first.optString("sourceUrl",GovernmentNotices.DIRECT_DHM);
   // Mark after notification only, not after a failed fetch.
   NotificationManager m=(NotificationManager)app.getSystemService(Context.NOTIFICATION_SERVICE);
   if(m==null)return Result.retry();
   final String channel="floodsafe_gov_bulletins";
   if(Build.VERSION.SDK_INT>=26)m.createNotificationChannel(new NotificationChannel(channel,"नेपाल सरकारका मौसम/बाढी सूचना",NotificationManager.IMPORTANCE_DEFAULT));
   PendingIntent open=PendingIntent.getActivity(app,1402,new Intent(Intent.ACTION_VIEW,Uri.parse(link)),
    PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
   String title="DHM / NDRRMA · "+a.length()+" लागू सरकारी सूचना";
   String body=first.optString("titleNe","सरकारी चेतावनी हेर्नुहोस्");
   Notification.Builder b=Build.VERSION.SDK_INT>=26?new Notification.Builder(app,channel):new Notification.Builder(app);
   b.setSmallIcon(android.R.drawable.ic_dialog_alert).setContentTitle(title).setContentText(body)
    .setStyle(new Notification.BigTextStyle().bigText(body+"\nमूल सरकारी प्रकाशनबाट पुष्टि गर्नुहोस्।"));
   // Android automatically removes a stale bulletin notification at its validity end,
   // even if background WorkManager is delayed or the user never taps the notice.
   if(Build.VERSION.SDK_INT>=26){
      long maxExpiry=0L;
      for(int i=0;i<a.length();i++){
         JSONObject item=a.optJSONObject(i);
         if(item!=null)maxExpiry=Math.max(maxExpiry,GovernmentNotices.time(item.optString("validUntil")));
      }
      if(maxExpiry>System.currentTimeMillis())b.setTimeoutAfter(maxExpiry-System.currentTimeMillis());
   }
   b
    .setAutoCancel(true).setContentIntent(open);
   m.notify(1402,b.build());p.edit().putString("latest",now).apply();
   return Result.success();
  }catch(Exception e){return Result.retry();}
 }
}