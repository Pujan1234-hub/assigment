package com.pjbuilts.floodsafefeedback;

import android.Manifest;
import android.app.*;
import android.app.job.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.os.Build;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import org.json.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.*;
import javax.crypto.spec.GCMParameterSpec;
import java.time.Instant;

public final class FeedbackAlerts extends JobService {
 private static final int JOB=14021;
 private static final String PREF="feedback_alerts", ALIAS="floodsafe_feedback_alerts", CHANNEL="feedback_updates";
 private volatile boolean stopped;
 private static android.content.SharedPreferences prefs(Context c){return c.getSharedPreferences(PREF,MODE_PRIVATE);}
 private static javax.crypto.SecretKey key()throws Exception{
  KeyStore ks=KeyStore.getInstance("AndroidKeyStore");ks.load(null);
  if(ks.containsAlias(ALIAS))return (javax.crypto.SecretKey)ks.getKey(ALIAS,null);
  KeyGenerator gen=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
  gen.init(new KeyGenParameterSpec.Builder(ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());
  return gen.generateKey();
 }
 private static String latest(JSONArray items){
  Instant max=Instant.EPOCH;
  for(int i=0;i<items.length();i++){JSONObject row=items.optJSONObject(i);if(row==null)continue;try{Instant at=Instant.parse(row.optString("created_at"));if(at.isAfter(max))max=at;}catch(Exception ignored){}}
  return max.toString();
 }
 static synchronized void enable(Context c,String token,JSONArray items)throws Exception{
  if(token.isEmpty())throw new IllegalArgumentException();
  Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.ENCRYPT_MODE,key());
  String iv=Base64.encodeToString(cipher.getIV(),Base64.NO_WRAP),encrypted=Base64.encodeToString(cipher.doFinal(token.getBytes(StandardCharsets.UTF_8)),Base64.NO_WRAP);
  String previous=prefs(c).getString("watermark",null);
  String baseline=previous==null?latest(items):previous;
  prefs(c).edit().putString("iv",iv).putString("cipher",encrypted).putString("watermark",baseline).commit();
  JobScheduler scheduler=c.getSystemService(JobScheduler.class);
  JobInfo job=new JobInfo.Builder(JOB,new ComponentName(c,FeedbackAlerts.class)).setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY).setPeriodic(15*60*1000L).setPersisted(true).build();
  try{if(scheduler.schedule(job)!=JobScheduler.RESULT_SUCCESS)throw new IllegalStateException("Scheduler rejected request");}catch(RuntimeException e){disable(c);throw e;}
 }
 static boolean enabled(Context c){JobScheduler s=c.getSystemService(JobScheduler.class);return s!=null&&s.getPendingJob(JOB)!=null&&!prefs(c).getString("cipher","").isEmpty();}
 static synchronized void disable(Context c){
  c.getSystemService(JobScheduler.class).cancel(JOB);prefs(c).edit().clear().commit();
  c.getSystemService(NotificationManager.class).cancel(JOB);
  try{KeyStore ks=KeyStore.getInstance("AndroidKeyStore");ks.load(null);ks.deleteEntry(ALIAS);}catch(Exception ignored){}
 }
 private static String readToken(Context c)throws Exception{
  String iv=prefs(c).getString("iv",""),encrypted=prefs(c).getString("cipher","");
  if(iv.isEmpty()||encrypted.isEmpty())return "";
  Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.DECRYPT_MODE,key(),new GCMParameterSpec(128,Base64.decode(iv,Base64.NO_WRAP)));
  return new String(cipher.doFinal(Base64.decode(encrypted,Base64.NO_WRAP)),StandardCharsets.UTF_8);
 }
 @Override public boolean onStartJob(JobParameters params){
  stopped=false;
  new Thread(()->{try{check();}catch(Exception ignored){}finally{if(!stopped)jobFinished(params,false);}},"feedback-background-check").start();
  return true;
 }
 @Override public boolean onStopJob(JobParameters params){stopped=true;return true;}
 private void check()throws Exception{
  String token=readToken(this);if(token.isEmpty()||stopped)return;
  HttpURLConnection c=(HttpURLConnection)new URL(MainActivity.API).openConnection();
  JSONArray items;
  try{
   c.setInstanceFollowRedirects(false);c.setConnectTimeout(12000);c.setReadTimeout(15000);c.setRequestProperty("Accept","application/json");c.setRequestProperty("x-admin-token",token);
   int status=c.getResponseCode();if(status==401||status==403){if(!stopped&&token.equals(readToken(this)))disable(this);return;}if(status!=200)return;
   try(InputStream in=c.getInputStream();ByteArrayOutputStream out=new ByteArrayOutputStream()){
    byte[] buf=new byte[4096];int n;while((n=in.read(buf))!=-1){if(out.size()+n>4_000_000)return;out.write(buf,0,n);}
    JSONObject obj=new JSONObject(out.toString(StandardCharsets.UTF_8.name()));if(!obj.optBoolean("ok"))return;items=obj.optJSONArray("items");if(items==null)return;
   }
  }finally{c.disconnect();}
  synchronized(FeedbackAlerts.class){
   if(stopped||!token.equals(readToken(this)))return;
   Instant prev=Instant.parse(prefs(this).getString("watermark",Instant.EPOCH.toString()));
   Instant now=Instant.parse(latest(items));
   if(!now.isAfter(prev))return;
   if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return;
   NotificationManager nm=getSystemService(NotificationManager.class);
   if(!nm.areNotificationsEnabled())return;
   nm.createNotificationChannel(new NotificationChannel(CHANNEL,"New website feedback",NotificationManager.IMPORTANCE_DEFAULT));
   if(nm.getNotificationChannel(CHANNEL).getImportance()==NotificationManager.IMPORTANCE_NONE)return;
   Intent open=new Intent(this,MainActivity.class);open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP);
   PendingIntent intent=PendingIntent.getActivity(this,JOB,open,PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);
   Notification notification=new Notification.Builder(this,CHANNEL).setSmallIcon(android.R.drawable.ic_dialog_email).setContentTitle("FloodSafe Feedback").setContentText("New website feedback received. Open the private inbox.").setVisibility(Notification.VISIBILITY_PRIVATE).setAutoCancel(true).setContentIntent(intent).build();
   nm.notify(JOB,notification);prefs(this).edit().putString("watermark",now.toString()).commit();
  }
 }
}
