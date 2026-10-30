package io.github.pujan1234hub.floodsafe.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.pm.PackageManager;
import android.os.SystemClock;
import com.google.android.play.core.appupdate.AppUpdateInfo;
import com.google.android.play.core.appupdate.AppUpdateManager;
import com.google.android.play.core.appupdate.AppUpdateManagerFactory;
import com.google.android.play.core.install.InstallStateUpdatedListener;
import com.google.android.play.core.install.model.AppUpdateType;
import com.google.android.play.core.install.model.InstallStatus;
import com.google.android.play.core.install.model.UpdateAvailability;

/**
 * Native code cannot safely be OTA patched. For Play-installed production builds,
 * ask Play to download a flexible update and offer restart after download.
 * Preview APK is deliberately excluded because Play cannot update its package.
 */
final class PlayStoreUpdateBridge {
    private static final int REQUEST_UPDATE=7091;
    private static final long CHECK_EVERY_MS=24L*60L*60L*1000L;
    private AppUpdateManager manager;
    private InstallStateUpdatedListener listener;
    private boolean connected=false,dialogShowing=false;
    private long lastCheckAt=0L;
    private final Activity activity;
    PlayStoreUpdateBridge(Activity a){activity=a;}
    void check(){
        if(activity==null||activity.isFinishing()||activity.isDestroyed())return;
        if(activity.getPackageName().endsWith(".preview"))return;
        try{
            String installer=activity.getPackageManager().getInstallerPackageName(activity.getPackageName());
            if(!"com.android.vending".equals(installer))return;
            if(manager==null)manager=AppUpdateManagerFactory.create(activity);
            if(!connected){
                listener=state->{
                    if(state.installStatus()==InstallStatus.DOWNLOADED)showRestartPrompt();
                };
                manager.registerListener(listener);connected=true;
            }
            long now=SystemClock.elapsedRealtime();
            if(lastCheckAt>0&&now-lastCheckAt<CHECK_EVERY_MS)return;
            lastCheckAt=now;
            manager.getAppUpdateInfo().addOnSuccessListener(info->{
                if(activity.isFinishing()||activity.isDestroyed())return;
                if(info.installStatus()==InstallStatus.DOWNLOADED){
                    showRestartPrompt();return;
                }
                if(info.updateAvailability()!=UpdateAvailability.UPDATE_AVAILABLE ||
                   !info.isUpdateTypeAllowed(AppUpdateType.FLEXIBLE))return;
                try{
                    // Play handles update consent, delivery, signature and installation.
                    manager.startUpdateFlowForResult(info,AppUpdateType.FLEXIBLE,activity,REQUEST_UPDATE);
                }catch(Exception ignored){}
            });
        }catch(Exception ignored){
            // A missing Play service must never block river safety monitoring.
        }
    }
    private void showRestartPrompt(){
        if(dialogShowing||activity.isFinishing()||activity.isDestroyed())return;
        dialogShowing=true;
        new AlertDialog.Builder(activity)
            .setTitle("FloodSafe Nepal update")
            .setMessage("Google Play बाट नयाँ Android version डाउनलोड भयो। सुरक्षित रूपमा लागू गर्न app पुनः सुरु गर्नुहोस्।")
            .setPositiveButton("Restart", (d,w)->{
                dialogShowing=false;
                try{if(manager!=null)manager.completeUpdate();}catch(Exception ignored){}
            })
            .setNegativeButton("Later",(d,w)->dialogShowing=false)
            .setOnCancelListener(d->dialogShowing=false)
            .show();
    }
    void close(){
        try{if(connected&&listener!=null&&manager!=null)manager.unregisterListener(listener);}catch(Exception ignored){}
        connected=false;listener=null;
    }
}
