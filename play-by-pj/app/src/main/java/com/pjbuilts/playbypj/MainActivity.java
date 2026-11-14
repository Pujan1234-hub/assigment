package com.pjbuilts.playbypj;

import android.app.Activity;
import android.Manifest;
import android.os.Build;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.content.Context;
import android.provider.MediaStore;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.animation.AccelerateDecelerateInterpolator;
import android.graphics.Canvas;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.List;
import java.util.Collections;
import java.util.Comparator;
import java.util.IdentityHashMap;
import java.util.Map;
import android.view.ViewParent;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.ColorMatrix;
import android.graphics.ColorMatrixColorFilter;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.OpenableColumns;
import android.content.res.AssetFileDescriptor;
import android.view.Gravity;
import org.videolan.libvlc.util.VLCVideoLayout;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.Toast;

import org.videolan.libvlc.LibVLC;
import org.videolan.libvlc.Media;
import org.videolan.libvlc.MediaPlayer;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Locale;

public final class MainActivity extends Activity {
    private static final int OPEN_FILM=3101, MUSIC_PERMISSION=3105;
    private static final int FULLSCREEN=0, LOOP_ONE=1, LOOP_ALL=2;
    private static final int CREAM=0xfffaf7ed, INK=0xff111925, SOFT=0xffeae3d8, GOLD=0xffd4a957;
    private LibVLC vlc;
    private MediaPlayer player;
    private AssetFileDescriptor openedFile;
    private Uri movieUri;
    private String movieUrl;
    private boolean retryingSoftware=false, seeking=false;
    private long videoDuration=0L;
    private int look=0, intensity=78, rateIndex=0;
    private final float[] rates={1f,1.25f,1.5f,2f,0.75f};
    private final String[] looks={"Original","Cinema Gold","Vivid 4K","Noir"};
    private final Handler ui=new Handler(Looper.getMainLooper());
    private VLCVideoLayout videoLayout;
    private boolean videoAttached=false, pendingPlay=false;
    private int outputAttachAttempts=0;
    private View tint;
    private SeekBar timeline,filterAmount;
    private TextView startClock,endClock,status,mediaTitle,codecLabel,rateLabel;
    private Button playButton,rateButton,fullPlay,loopButton,subtitleButton,audioButton;
    private final ArrayList<Button> lookButtons=new ArrayList<>();
    private boolean immersive=false,isMusic=false;
    private int loopMode=FULLSCREEN,queueIndex=-1,musicListLimit=80;
    private final List<MusicLibrary.Track> music=new ArrayList<>();
    private final List<MusicLibrary.Track> queue=new ArrayList<>();
    private MusicLibrary.Track currentTrack;
    private View musicResults;
    private LinearLayout musicResultsPanel;
    private EditText musicSearch;
    private TextView musicCount;
    private ScrollView rootScroll;
    private LinearLayout rootPage;
    private FrameLayout videoBox,fullHud;
    private MusicWaveView musicWave;
    private Button fullExit;
    private final Map<View,Integer> originalVis=new IdentityHashMap<>();
    private boolean controlsShown=true;
    private final Runnable hideFullControls=()->{
        if(immersive&&fullHud!=null){
            fullHud.animate().alpha(0f).setDuration(250).withEndAction(()->{
                if(immersive)fullHud.setVisibility(View.INVISIBLE);
            }).start();
            controlsShown=false;
        }
    };
    private final Runnable attachVideoOutput=new Runnable(){
        @Override public void run(){
            if(player==null||videoLayout==null||isFinishing()||isDestroyed())return;
            if(videoAttached&&player.getVLCVout().areViewsAttached())return;
            // attachViews requires an attached layout; attaching before the view is
            // measured is what left the prior player in an invalid surface state.
            if(videoLayout.getWindowToken()==null||videoLayout.getWidth()==0||videoLayout.getHeight()==0){
                if(++outputAttachAttempts<60)ui.postDelayed(this,80L);
                else status.setText("Video surface not ready • reopen player");
                return;
            }
            try{
                if(!player.getVLCVout().areViewsAttached()){
                    // Canonical VideoLAN VideoHelper manages TextureView lifecycle,
                    // surface recreation, vout and subtitles without duplicate attach.
                    player.attachViews(videoLayout,null,false,true);
                }
                videoAttached=true;
                outputAttachAttempts=0;
                status.setText("VLC video output ready • MP4 / HEVC / MKV");
                if(pendingPlay){
                    pendingPlay=false;
                    playMedia(false);
                }
            }catch(Exception e){
                videoAttached=false;
                if(++outputAttachAttempts<12){
                    ui.postDelayed(this,160L);
                }else{
                    status.setText("VLC surface error: "+e.getClass().getSimpleName());
                }
            }
        }
    };
    private final Runnable tick=new Runnable(){
        @Override public void run(){
            if(player!=null&&!seeking){
                long len=player.getLength(),time=player.getTime();
                if(len>0){videoDuration=len;timeline.setMax(1000);timeline.setProgress((int)Math.max(0,Math.min(1000,time*1000L/len)));}
                startClock.setText(clock(Math.max(0,time)));
                endClock.setText(clock(Math.max(0,len)));
            }
            ui.postDelayed(this,450L);
        }
    };

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().setStatusBarColor(CREAM);
        getWindow().setNavigationBarColor(INK);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        buildScreen();
        try{
            ArrayList<String> opts=new ArrayList<>();
            opts.add("--no-drop-late-frames");
            opts.add("--no-skip-frames");
            opts.add("--network-caching=850");
            opts.add("--file-caching=500");
            opts.add("--audio-time-stretch");
            vlc=new LibVLC(getApplicationContext(),opts);
            player=new MediaPlayer(vlc);
            player.setEventListener(event->ui.post(()->handleEvent(event.type)));
            // Never attach the VLC output inside onCreate before the layout is ready.
            // Keep pending file/stream requests until VideoLAN has attached its vout.
            status.setText("Preparing VLC video output…");
            videoLayout.post(attachVideoOutput);
            ui.post(tick);
            if(getIntent()!=null&&Intent.ACTION_VIEW.equals(getIntent().getAction())){
                Uri u=getIntent().getData();if(u!=null)openFilm(u);
            }
        }catch(Exception | UnsatisfiedLinkError ex){
            status.setText("VLC engine could not start: "+ex.getClass().getSimpleName());
            toast("VLC initialization failed");
        }
    }

    private void buildScreen(){
        rootScroll=new ScrollView(this);
        rootScroll.setFillViewport(true);
        rootScroll.setBackgroundColor(CREAM);
        rootPage=new LinearLayout(this);rootPage.setOrientation(LinearLayout.VERTICAL);
        rootPage.setPadding(dp(16),dp(22),dp(16),dp(42));
        rootScroll.addView(rootPage);
        setContentView(rootScroll);
        LinearLayout page=rootPage;

        TextView title=text("PLAY  by PJ",33,true,INK);page.addView(title);
        TextView brand=text("PJBUILTS  ·  PRIVATE CINEMA  ·  VLC DECODER",12,true,0xff85745f);
        LinearLayout.LayoutParams bp=vertical(0,10);page.addView(brand,bp);

        LinearLayout sourceRow=new LinearLayout(this);sourceRow.setOrientation(LinearLayout.HORIZONTAL);
        LinearLayout.LayoutParams sr=vertical(0,20);page.addView(sourceRow,sr);
        Button open=button("+  Open Film",INK,Color.WHITE,17);
        Button stream=button("↗  Stream",SOFT,INK,17);
        LinearLayout.LayoutParams a=new LinearLayout.LayoutParams(0,dp(56),1);
        a.setMargins(0,0,dp(7),0);
        LinearLayout.LayoutParams b=new LinearLayout.LayoutParams(0,dp(56),1);
        b.setMargins(dp(7),0,0,0);
        sourceRow.addView(open,a);sourceRow.addView(stream,b);
        open.setOnClickListener(v->pickFilm());
        stream.setOnClickListener(v->streamDialog());

        mediaTitle=text("Choose a film to start",16,true,INK);page.addView(mediaTitle,vertical(0,20));
        videoBox=new FrameLayout(this){
            @Override protected void onMeasure(int w,int h){
                int ww=View.MeasureSpec.getSize(w);
                int hh=immersive?Math.max(dp(220),getResources().getDisplayMetrics().heightPixels):
                    Math.round(ww*0.73f);
                super.onMeasure(w,View.MeasureSpec.makeMeasureSpec(hh,View.MeasureSpec.EXACTLY));
            }
        };
        videoBox.setBackground(round(INK,18));
        videoBox.setClipToOutline(true);
        page.addView(videoBox,new LinearLayout.LayoutParams(-1,-2));
        videoLayout=new VLCVideoLayout(this);
        videoBox.addView(videoLayout,new FrameLayout.LayoutParams(-1,-1));
        musicWave=new MusicWaveView(this);
        musicWave.setActive(false);
        videoBox.addView(musicWave,new FrameLayout.LayoutParams(-1,-1));
        tint=new View(this);tint.setClickable(false);
        videoBox.addView(tint,new FrameLayout.LayoutParams(-1,-1));
        installFullscreenControls();
        videoLayout.setOnClickListener(v->{if(immersive)showFullscreenControls();});
        musicWave.setOnClickListener(v->{if(immersive)showFullscreenControls();});
        status=text("Starting VLC decoder…",12,false,0xff7b6b57);
        page.addView(status,vertical(0,9));

        LinearLayout times=new LinearLayout(this);times.setOrientation(LinearLayout.HORIZONTAL);
        startClock=text("00:00",13,true,INK);endClock=text("00:00",13,true,INK);
        times.addView(startClock,new LinearLayout.LayoutParams(0,-2,1));
        endClock.setGravity(Gravity.END);times.addView(endClock,new LinearLayout.LayoutParams(0,-2,1));
        page.addView(times,vertical(0,18));
        timeline=new SeekBar(this);timeline.setMax(1000);
        timeline.setProgressTintList(android.content.res.ColorStateList.valueOf(GOLD));
        timeline.setThumbTintList(android.content.res.ColorStateList.valueOf(GOLD));
        page.addView(timeline,vertical(0,8));
        timeline.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onProgressChanged(SeekBar bar,int value,boolean fromUser){}
            public void onStartTrackingTouch(SeekBar bar){seeking=true;}
            public void onStopTrackingTouch(SeekBar bar){
                seeking=false;
                if(player!=null&&player.isSeekable()&&player.getLength()>0)
                    player.setTime(player.getLength()*bar.getProgress()/1000L);
            }
        });

        LinearLayout controls=new LinearLayout(this);controls.setOrientation(LinearLayout.HORIZONTAL);
        page.addView(controls,vertical(0,8));
        Button back=button("−10",SOFT,INK,16);
        playButton=button("▶",INK,GOLD,18);
        Button ahead=button("+10",SOFT,INK,16);
        rateButton=button("1×",SOFT,INK,16);
        Button full=button("⛶",SOFT,INK,19);
        for(Button v:new Button[]{back,playButton,ahead,rateButton,full}){
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(53),1);
            lp.setMargins(dp(2),0,dp(2),0);controls.addView(v,lp);
        }
        back.setOnClickListener(v->seekRelative(-10000L));
        ahead.setOnClickListener(v->seekRelative(10000L));
        playButton.setOnClickListener(v->togglePlay());
        rateButton.setOnClickListener(v->{rateIndex=(rateIndex+1)%rates.length;
            if(player!=null)player.setRate(rates[rateIndex]);
            rateButton.setText(String.format(Locale.US,"%s×",rates[rateIndex]==1?"1":String.valueOf(rates[rateIndex])));
        });
        full.setOnClickListener(v->toggleFullscreen());

        LinearLayout extras=new LinearLayout(this);
        extras.setOrientation(LinearLayout.HORIZONTAL);
        page.addView(extras,vertical(0,9));
        subtitleButton=button("CC Subtitles",SOFT,INK,12);
        audioButton=button("♫ Audio tracks",SOFT,INK,12);
        loopButton=button("↻ Loop: Off",SOFT,INK,12);
        for(Button v:new Button[]{subtitleButton,audioButton,loopButton}){
            LinearLayout.LayoutParams ep=new LinearLayout.LayoutParams(0,dp(48),1f);
            ep.setMargins(dp(2),0,dp(2),0);
            extras.addView(v,ep);
        }
        subtitleButton.setOnClickListener(v->showTrackDialog(true));
        audioButton.setOnClickListener(v->showTrackDialog(false));
        loopButton.setOnClickListener(v->cycleLoop());
        page.addView(text("✦  CINEMATIC LOOKS",16,true,INK),vertical(0,22));
        LinearLayout filters=new LinearLayout(this);filters.setOrientation(LinearLayout.HORIZONTAL);
        page.addView(filters,vertical(0,10));
        for(int i=0;i<looks.length;i++){
            final int choice=i;
            Button v=button(looks[i],i==0?INK:SOFT,i==0?Color.WHITE:INK,12);
            lookButtons.add(v);
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(48),i==1?1.45f:1f);
            lp.setMargins(dp(2),0,dp(2),0);filters.addView(v,lp);
            v.setOnClickListener(bv->{
                look=choice;
                applyLook(true);
                v.animate().scaleX(1.07f).scaleY(1.07f).setDuration(130)
                    .withEndAction(()->v.animate().scaleX(1f).scaleY(1f).setDuration(160).start())
                    .start();
            });
        }
        page.addView(text("Filter intensity",13,true,INK),vertical(0,15));
        filterAmount=new SeekBar(this);filterAmount.setMax(100);filterAmount.setProgress(intensity);
        filterAmount.setProgressTintList(android.content.res.ColorStateList.valueOf(GOLD));
        filterAmount.setThumbTintList(android.content.res.ColorStateList.valueOf(0xff008980));
        page.addView(filterAmount);
        filterAmount.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onProgressChanged(SeekBar bar,int n,boolean user){intensity=n;applyLook();}
            public void onStartTrackingTouch(SeekBar bar){}
            public void onStopTrackingTouch(SeekBar bar){}
        });
        codecLabel=text("VLC · Hardware decode + software fallback · MP4 / HEVC / MKV",12,true,0xff7b6b57);
        page.addView(codecLabel,vertical(0,20));
        buildMusicSection(page);
        TextView footer=text("Hardware when available · Software codec fallback · Local private playback\nPJBUILTS.COM · Your films remain on your device",11,false,0xff948879);
        footer.setGravity(Gravity.CENTER);page.addView(footer,vertical(0,20));
    }

    private void pickFilm(){
        Intent picker=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        picker.addCategory(Intent.CATEGORY_OPENABLE);
        picker.setType("*/*"); // Include MKV and HEVC even when provider reports octet-stream
        picker.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        try{startActivityForResult(picker,OPEN_FILM);}
        catch(ActivityNotFoundException e){toast("No document picker available");}
    }
    @Override protected void onActivityResult(int req,int result,Intent data){
        super.onActivityResult(req,result,data);
        if(req!=OPEN_FILM||result!=RESULT_OK||data==null||data.getData()==null)return;
        Uri uri=data.getData();
        try{getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(Exception ignored){}
        openFilm(uri);
    }
    private void openFilm(Uri uri){
        movieUri=uri;movieUrl=null;retryingSoftware=false;
        mediaTitle.setText(displayName(uri));
        playMedia(false);
    }
    private void streamDialog(){
        EditText edit=new EditText(this);
        edit.setSingleLine(true);edit.setHint("https://example.com/film.m3u8");
        edit.setInputType(android.text.InputType.TYPE_TEXT_VARIATION_URI);
        new AlertDialog.Builder(this).setTitle("Stream URL")
            .setView(edit).setPositiveButton("Play",(d,w)->{
                String url=edit.getText().toString().trim();
                if(!(url.startsWith("https://")||url.startsWith("http://"))){
                    toast("Enter an http(s) media URL");return;
                }
                movieUrl=url;movieUri=null;retryingSoftware=false;
                mediaTitle.setText("Stream");
                playMedia(false);
            }).setNegativeButton("Cancel",null).show();
    }
    private void playMedia(boolean softwareOnly){
        if(vlc==null||player==null)return;
        if(!videoAttached||!player.getVLCVout().areViewsAttached()){
            pendingPlay=true;
            status.setText("Preparing video screen before decoding…");
            ui.removeCallbacks(attachVideoOutput);
            ui.post(attachVideoOutput);
            return;
        }
        closeOpenedFile();
        try{
            Media media;
            if(movieUri!=null && "content".equalsIgnoreCase(movieUri.getScheme())){
                // SAF URIs aren't filesystem paths. Hand VLC the actual seekable FD,
                // not a content:// string that its native demuxer can't open.
                openedFile=getContentResolver().openAssetFileDescriptor(movieUri,"r");
                if(openedFile!=null)media=new Media(vlc,openedFile);
                else media=new Media(vlc,movieUri);
            }else if(movieUri!=null){
                media=new Media(vlc,movieUri);
            }else if(movieUrl!=null){
                media=new Media(vlc,Uri.parse(movieUrl));
            }else return;
            media.setHWDecoderEnabled(!softwareOnly,false);
            media.addOption(":network-caching=850");
            media.addOption(":file-caching=500");
            media.addOption(":no-audio-time-stretch=0");
            player.stop();
            player.setMedia(media);
            media.release();
            player.play();
            status.setText(softwareOnly?"Trying VLC software decoder…":"Opening with VLC decoder…");
            codecLabel.setText(softwareOnly?"VLC · SOFTWARE decoder (fallback)":"VLC · Hardware decode with software fallback");
        }catch(Exception e){
            if(!softwareOnly){retryingSoftware=true;playMedia(true);}
            else{
                status.setText("Could not open file: "+e.getClass().getSimpleName());
                toast("This file could not be opened");
            }
        }
    }
    private void handleEvent(int type){
        if(isFinishing()||player==null)return;
        if(type==MediaPlayer.Event.Playing){
            playButton.setText("Ⅱ");
            status.setText(retryingSoftware?"Playing • VLC software decode":"Playing • VLC decoder");
        }else if(type==MediaPlayer.Event.Paused||type==MediaPlayer.Event.Stopped||type==MediaPlayer.Event.EndReached){
            playButton.setText("▶");
            if(type==MediaPlayer.Event.EndReached)status.setText("Playback finished");
        }else if(type==MediaPlayer.Event.EncounteredError){
            if(!retryingSoftware&&(movieUri!=null||movieUrl!=null)){
                retryingSoftware=true;
                status.setText("Decoder error — retrying in software…");
                ui.postDelayed(()->playMedia(true),240);
            }else{
                status.setText("Unable to decode this file with VLC • Check format/source");
                toast("Decoder failed • try another file or source");
            }
        }
    }
    private void togglePlay(){
        if(player==null)return;
        if(player.isPlaying())player.pause();
        else if(movieUri!=null||movieUrl!=null)player.play();
        else pickFilm();
    }
    private void seekRelative(long delta){
        if(player==null||!player.isSeekable())return;
        long length=player.getLength();
        player.setTime(Math.max(0,length>0?Math.min(length,player.getTime()+delta):player.getTime()+delta));
    }
    private void toggleFullscreen(){
        immersive=!immersive;
        if(immersive){
            getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN|
                View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
        }else getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR);
    }
    private void applyLook(){
        float k=intensity/100f;
        int mask=Color.TRANSPARENT;
        if(look==1)mask=Color.argb((int)(48*k),241,187,95);
        else if(look==2)mask=Color.argb((int)(32*k),35,213,180);
        else if(look==3)mask=Color.argb((int)(35*k),0,0,0);
        tint.setBackgroundColor(mask);
        Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
        ColorMatrix m=new ColorMatrix();
        if(look==3)m.setSaturation(1f-k);
        else if(look==2)m.setSaturation(1f+0.45f*k);
        else if(look==1)m.setSaturation(1f+0.12f*k);
        paint.setColorFilter(new ColorMatrixColorFilter(m));
        // The LibVLC layout uses its own TextureView for GPU rendering;
        // keep filter effects on the containing native video view.
        videoLayout.setLayerType(View.LAYER_TYPE_HARDWARE,paint);
        videoLayout.setLayerPaint(paint);
        for(int i=0;i<lookButtons.size();i++){
            Button b=lookButtons.get(i);
            b.setBackground(round(i==look?INK:SOFT,16));
            b.setTextColor(i==look?Color.WHITE:INK);
        }
    }
    private void closeOpenedFile(){
        if(openedFile!=null){try{openedFile.close();}catch(IOException ignored){} openedFile=null;}
    }
    private String displayName(Uri uri){
        String name=uri.getLastPathSegment();
        if("content".equalsIgnoreCase(uri.getScheme())){
            try(Cursor c=getContentResolver().query(uri,new String[]{OpenableColumns.DISPLAY_NAME},null,null,null)){
                if(c!=null&&c.moveToFirst())name=c.getString(0);
            }catch(Exception ignored){}
        }
        return name==null?"Selected film":name;
    }
    private static String clock(long milli){
        long s=milli/1000;
        return s>=3600?String.format(Locale.US,"%d:%02d:%02d",s/3600,(s%3600)/60,s%60):
                String.format(Locale.US,"%02d:%02d",s/60,s%60);
    }
    private Button button(String label,int bg,int fg,int sp){
        Button b=new Button(this);
        b.setAllCaps(false);b.setText(label);b.setTextSize(sp);
        b.setTextColor(fg);b.setBackground(round(bg,16));
        b.setPadding(dp(4),0,dp(4),0);
        b.setTypeface(android.graphics.Typeface.DEFAULT,android.graphics.Typeface.BOLD);
        return b;
    }
    private TextView text(String label,int sp,boolean bold,int color){
        TextView t=new TextView(this);t.setText(label);t.setTextSize(sp);
        t.setTextColor(color);
        if(bold)t.setTypeface(android.graphics.Typeface.DEFAULT,android.graphics.Typeface.BOLD);
        return t;
    }
    private GradientDrawable round(int color,int radius){
        GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(radius));return d;
    }
    private LinearLayout.LayoutParams vertical(int top,int bottom){
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.setMargins(0,dp(top),0,dp(bottom));return p;
    }
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
    private void toast(String msg){Toast.makeText(this,msg,Toast.LENGTH_LONG).show();}
    @Override protected void onResume(){
        super.onResume();
        if(player!=null&&(!videoAttached||!player.getVLCVout().areViewsAttached())){
            videoAttached=false;
            ui.post(attachVideoOutput);
        }
    }
    @Override protected void onPause(){
        super.onPause();
        if(player!=null&&player.isPlaying())player.pause();
    }
    @Override protected void onDestroy(){
        ui.removeCallbacksAndMessages(null);
        try{
            if(player!=null){
                player.setEventListener(null);
                player.stop();
                // VideoHelper must be released through the canonical player API.
                player.detachViews();
                player.release();
            }
        }catch(Exception ignored){}
        videoAttached=false;
        closeOpenedFile();
        if(vlc!=null)vlc.release();
        super.onDestroy();
    }
}
