package com.pjbuilts.floodsafefeedback;
import android.content.Context;
import com.google.firebase.messaging.FirebaseMessaging;
import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;
import org.json.JSONObject;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.concurrent.Executors;
import java.util.concurrent.ExecutorService;

public final class FeedbackPushService extends FirebaseMessagingService {
 private static final ExecutorService io=Executors.newSingleThreadExecutor();
 private static long lastAttempt=0;
 private static boolean syncing=false;
 private static volatile String state="Not registered";
 static String status(){return state;}
 static synchronized void sync(Context context,String admin,boolean force){
  Context c=context.getApplicationContext();
  if(admin.isEmpty()||!FeedbackAlerts.enabled(c)||syncing)return;
  if(!force&&System.currentTimeMillis()-lastAttempt<15*60*1000L)return;
  syncing=true;lastAttempt=System.currentTimeMillis();state="Registering device…";
  try{
   FirebaseMessaging.getInstance().getToken().addOnCompleteListener(task->{
    if(!task.isSuccessful()){state="Firebase registration failed";synchronized(FeedbackPushService.class){syncing=false;lastAttempt=0;}return;}
    String device=task.getResult();
    io.execute(()->{try{if(admin.equals(TokenStore.read(c))&&FeedbackAlerts.enabled(c)){JSONObject result=send(admin,device,"register_push");state=result.optBoolean("push_configured")?"Instant push registered":"Registered · server key pending";}}catch(Exception ignored){state="Registration failed · retrying";synchronized(FeedbackPushService.class){lastAttempt=0;}}finally{synchronized(FeedbackPushService.class){syncing=false;}}});
   });
  }catch(Exception e){syncing=false;}
 }
 static void unregister(Context context,String admin){
  state="Disabled";if(admin.isEmpty())return;
  io.execute(()->{try{send(admin,"","unregister_push");}catch(Exception ignored){}});
 }
 private static JSONObject send(String admin,String device,String action)throws Exception{
  HttpURLConnection c=(HttpURLConnection)new URL(MainActivity.API).openConnection();
  try{
   c.setInstanceFollowRedirects(false);c.setConnectTimeout(10000);c.setReadTimeout(10000);c.setRequestMethod("PATCH");c.setDoOutput(true);c.setRequestProperty("x-admin-token",admin);c.setRequestProperty("Content-Type","application/json");
   byte[] body=new JSONObject().put("action",action).put("fcm_token",device).toString().getBytes(StandardCharsets.UTF_8);c.setFixedLengthStreamingMode(body.length);
   try(OutputStream out=c.getOutputStream()){out.write(body);}
   if(c.getResponseCode()!=200)throw new IOException("Registration failed");
   try(InputStream in=c.getInputStream();ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] buf=new byte[1024];int n;while((n=in.read(buf))!=-1){if(out.size()+n>16384)throw new IOException("Response too large");out.write(buf,0,n);}return new JSONObject(out.toString(StandardCharsets.UTF_8.name()));}
  }finally{c.disconnect();}
 }
 @Override public void onNewToken(String device){String admin=TokenStore.read(this);if(!admin.isEmpty()&&FeedbackAlerts.enabled(this))sync(this,admin,true);}
 @Override public void onMessageReceived(RemoteMessage msg){
  if(!"website_feedback".equals(msg.getData().get("kind")))return;
  try{FeedbackAlerts.notifyAt(this,Instant.parse(msg.getData().get("created_at")));}catch(Exception ignored){}
 }
}
