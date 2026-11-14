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


    private void installFullscreenControls(){
        fullHud=new FrameLayout(this);
        fullHud.setVisibility(View.GONE);
        videoBox.addView(fullHud,new FrameLayout.LayoutParams(-1,-1));
        fullExit=button("✕ Exit Fullscreen",0xcc14202e,Color.WHITE,12);
        FrameLayout.LayoutParams top=new FrameLayout.LayoutParams(dp(166),dp(48),Gravity.TOP|Gravity.END);
        top.setMargins(dp(12),dp(12),dp(12),0);
        fullHud.addView(fullExit,top);
        fullExit.setOnClickListener(v->toggleFullscreen());
        LinearLayout bottom=new LinearLayout(this);
        bottom.setGravity(Gravity.CENTER);
        bottom.setOrientation(LinearLayout.HORIZONTAL);
        bottom.setPadding(dp(12),dp(7),dp(12),dp(13));
        bottom.setBackgroundColor(0xc5121b2b);
        FrameLayout.LayoutParams bp=new FrameLayout.LayoutParams(-1,dp(64),Gravity.BOTTOM);
        fullHud.addView(bottom,bp);
        Button rewind=button("−10",0xff29374b,Color.WHITE,13);
        fullPlay=button("▶",GOLD,INK,16);
        Button forward=button("+10",0xff29374b,Color.WHITE,13);
        Button sub=button("CC",0xff29374b,Color.WHITE,13);
        Button aud=button("♫",0xff29374b,Color.WHITE,13);
        Button again=button("↻",0xff29374b,Color.WHITE,13);
        for(Button b:new Button[]{rewind,fullPlay,forward,sub,aud,again}){
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(43),1);
            lp.setMargins(dp(3),0,dp(3),0);
            bottom.addView(b,lp);
        }
        rewind.setOnClickListener(v->{seekRelative(-10_000);showFullscreenControls();});
        fullPlay.setOnClickListener(v->{togglePlay();showFullscreenControls();});
        forward.setOnClickListener(v->{seekRelative(10_000);showFullscreenControls();});
        sub.setOnClickListener(v->{showTrackDialog(true);showFullscreenControls();});
        aud.setOnClickListener(v->{showTrackDialog(false);showFullscreenControls();});
        again.setOnClickListener(v->{cycleLoop();showFullscreenControls();});
    }
    private void showFullscreenControls(){
        if(!immersive||fullHud==null)return;
        ui.removeCallbacks(hideFullControls);
        fullHud.animate().cancel();
        fullHud.setVisibility(View.VISIBLE);
        fullHud.setAlpha(0f);
        fullHud.animate().alpha(1f).setDuration(200).start();
        controlsShown=true;
        ui.postDelayed(hideFullControls,4500);
    }
    private void showTrackDialog(boolean subtitles){
        if(player==null||!player.hasMedia()){
            toast("Open and start a film first");
            return;
        }
        List<VlcTrackPicker.Option> tracks=VlcTrackPicker.available(player,subtitles);
        String selected=VlcTrackPicker.selected(player,subtitles);
        ArrayList<String> display=new ArrayList<>();
        ArrayList<String> ids=new ArrayList<>();
        if(subtitles){
            display.add("Off · No subtitles");
            ids.add("-1");
        }
        for(int i=0;i<tracks.size();i++){
            VlcTrackPicker.Option t=tracks.get(i);
            if("-1".equals(t.id)&&subtitles)continue;
            display.add(String.format(Locale.US,"%02d · %s",i+1,t.label));
            ids.add(t.id);
        }
        if(tracks.isEmpty()&&!subtitles){
            new AlertDialog.Builder(this).setTitle("Audio tracks")
                .setMessage("The playing file has not reported an audio track yet.")
                .setPositiveButton("OK",null).show();
            return;
        }
        int checked=ids.indexOf(selected);
        if(checked<0)checked=subtitles?0:-1;
        String[] options=display.toArray(new String[0]);
        new AlertDialog.Builder(this)
            .setTitle(subtitles?"CC · Subtitle tracks":"♫ · Audio tracks")
            .setSingleChoiceItems(options,checked,(dialog,which)->{
                if(which>=0&&which<ids.size()){
                    boolean success=VlcTrackPicker.choose(player,subtitles,ids.get(which));
                    if(!success)toast("Track not available • try after playback starts");
                    else toast(subtitles?"Subtitle selected":"Audio track selected");
                }
                dialog.dismiss();
            })
            .setNegativeButton("Close",null).show();
    }
    private void cycleLoop(){
        loopMode=(loopMode+1)%3;
        String name=loopMode==LOOP_ONE?"One":loopMode==LOOP_ALL?"All":"Off";
        if(loopButton!=null){
            loopButton.setText("↻ Loop: "+name);
            loopButton.animate().rotationBy(180f).setDuration(220).start();
        }
        toast("Loop "+name);
    }
    private void buildMusicSection(LinearLayout page){
        TextView section=text("♫  YOUR MUSIC · A–Z LIBRARY",17,true,INK);
        page.addView(section,vertical(0,24));
        LinearLayout row=new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        page.addView(row,vertical(0,10));
        Button scan=button("↻ Music Library",INK,Color.WHITE,13);
        Button playlists=button("☷ Playlists",SOFT,INK,13);
        Button add=button("+ Save Song",SOFT,INK,13);
        for(Button b:new Button[]{scan,playlists,add}){
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(51),1);
            lp.setMargins(dp(2),0,dp(2),0);row.addView(b,lp);
        }
        scan.setOnClickListener(v->loadMusicLibrary());
        playlists.setOnClickListener(v->showPlaylists());
        add.setOnClickListener(v->saveCurrentToPlaylist());
        musicSearch=new EditText(this);
        musicSearch.setSingleLine(true);
        musicSearch.setTextSize(14);
        musicSearch.setHint("Search local songs A–Z");
        musicSearch.setBackground(round(0xffe9e4dc,12));
        musicSearch.setPadding(dp(12),0,dp(12),0);
        page.addView(musicSearch,new LinearLayout.LayoutParams(-1,dp(45)));
        musicSearch.addTextChangedListener(new TextWatcher(){
            public void beforeTextChanged(CharSequence s,int start,int count,int after){}
            public void onTextChanged(CharSequence s,int start,int before,int count){
                musicListLimit=80;showMusicItems();
            }
            public void afterTextChanged(Editable e){}
        });
        musicCount=text("Tap Music Library to grant access and load downloaded songs",12,false,0xff756b61);
        page.addView(musicCount,vertical(0,8));
        musicResultsPanel=new LinearLayout(this);
        musicResultsPanel.setOrientation(LinearLayout.VERTICAL);
        page.addView(musicResultsPanel,vertical(0,3));
    }
    private String musicPermission(){
        return Build.VERSION.SDK_INT>=33?
            "android.permission.READ_MEDIA_AUDIO":"android.permission.READ_EXTERNAL_STORAGE";
    }
    private void loadMusicLibrary(){
        String permission=musicPermission();
        if(Build.VERSION.SDK_INT>=23 && checkSelfPermission(permission)!=PackageManager.PERMISSION_GRANTED){
            requestPermissions(new String[]{permission},MUSIC_PERMISSION);
            return;
        }
        musicCount.setText("Scanning on-device music…");
        new Thread(()->{
            List<MusicLibrary.Track> found=MusicLibrary.scan(getApplicationContext());
            runOnUiThread(()->{
                if(isFinishing()||isDestroyed())return;
                music.clear();music.addAll(found);
                musicListLimit=80;showMusicItems();
            });
        },"PJ-Music-MediaStore").start();
    }
    @Override public void onRequestPermissionsResult(int req,String[] permissions,int[] results){
        super.onRequestPermissionsResult(req,permissions,results);
        if(req==MUSIC_PERMISSION){
            if(results.length>0&&results[0]==PackageManager.PERMISSION_GRANTED)loadMusicLibrary();
            else toast("Music access not granted; you can still open individual files");
        }
    }
    private void showMusicItems(){
        if(musicResultsPanel==null||musicCount==null||musicSearch==null)return;
        musicResultsPanel.removeAllViews();
        String query=musicSearch.getText().toString().toLowerCase(Locale.ROOT).trim();
        ArrayList<MusicLibrary.Track> filtered=new ArrayList<>();
        for(MusicLibrary.Track t:music)
            if(query.isEmpty()||t.name.toLowerCase(Locale.ROOT).contains(query))filtered.add(t);
        musicCount.setText(filtered.size()+" tracks · A–Z · on this device");
        int visible=Math.min(filtered.size(),musicListLimit);
        for(int i=0;i<visible;i++){
            final MusicLibrary.Track track=filtered.get(i);
            final List<MusicLibrary.Track> group=filtered;
            Button item=button("♫  "+track.name,0xfff1ede4,INK,12);
            item.setGravity(Gravity.START|Gravity.CENTER_VERTICAL);
            item.setSingleLine(true);item.setEllipsize(android.text.TextUtils.TruncateAt.END);
            LinearLayout.LayoutParams lp=vertical(0,3);lp.height=dp(48);
            musicResultsPanel.addView(item,lp);
            item.setOnClickListener(v->playTrack(track,group));
        }
        if(visible<filtered.size()){
            Button more=button("Show more · "+(filtered.size()-visible)+" remaining",SOFT,INK,12);
            musicResultsPanel.addView(more,vertical(4,8));
            more.setOnClickListener(v->{musicListLimit+=80;showMusicItems();});
        }
    }
    private void playTrack(MusicLibrary.Track track,List<MusicLibrary.Track> tracks){
        if(track==null)return;
        queue.clear();queue.addAll(tracks);
        queueIndex=0;
        for(int i=0;i<queue.size();i++)if(queue.get(i).uri.equals(track.uri)){queueIndex=i;break;}
        playQueueIndex(queueIndex);
    }
    private void playQueueIndex(int index){
        if(index<0||index>=queue.size())return;
        queueIndex=index;
        currentTrack=queue.get(index);
        isMusic=true;
        musicWave.setActive(true);
        movieUri=currentTrack.uri;
        movieUrl=null;retryingSoftware=false;
        mediaTitle.setText("♫  "+currentTrack.name);
        status.setText("Loading music · "+(queueIndex+1)+" / "+queue.size());
        playMedia(false);
    }
    private void showPlaylists(){
        List<String> names=MusicLibrary.names(this);
        ArrayList<String> opts=new ArrayList<>();
        opts.add("＋ Create new playlist");
        for(String name:names)opts.add("♫ "+name);
        new AlertDialog.Builder(this)
            .setTitle("My playlists · saved on this phone")
            .setItems(opts.toArray(new String[0]),(d,i)->{
                if(i==0)createPlaylistDialog(false);
                else{
                    String name=names.get(i-1);
                    List<MusicLibrary.Track> tracks=MusicLibrary.tracks(this,name);
                    if(tracks.isEmpty()){toast("Playlist is empty");return;}
                    playTrack(tracks.get(0),tracks);
                    toast("Playing "+name+" · "+tracks.size()+" tracks");
                }
            }).setNegativeButton("Close",null).show();
    }
    private void createPlaylistDialog(boolean addCurrent){
        EditText field=new EditText(this);
        field.setSingleLine(true);
        field.setHint("e.g. My favourites");
        new AlertDialog.Builder(this)
            .setTitle("Create playlist")
            .setView(field)
            .setPositiveButton("Create",(d,w)->{
                String name=field.getText().toString().trim();
                boolean created=MusicLibrary.create(this,name);
                if(!created){toast("Name required or playlist already exists");return;}
                if(addCurrent&&currentTrack!=null)MusicLibrary.add(this,name,currentTrack);
                toast("Playlist saved: "+name);
            }).setNegativeButton("Cancel",null).show();
    }
    private void saveCurrentToPlaylist(){
        if(currentTrack==null){toast("Play a music file from Music Library first");return;}
        List<String> names=MusicLibrary.names(this);
        ArrayList<String> choices=new ArrayList<>();
        choices.add("＋ New playlist");
        choices.addAll(names);
        new AlertDialog.Builder(this).setTitle("Save song to playlist")
            .setItems(choices.toArray(new String[0]),(d,which)->{
                if(which==0)createPlaylistDialog(true);
                else{
                    String name=names.get(which-1);
                    if(MusicLibrary.add(this,name,currentTrack))toast("Saved to "+name);
                    else toast("Unable to save track");
                }
            }).setNegativeButton("Cancel",null).show();
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
        isMusic=false;currentTrack=null;
        queue.clear();queueIndex=-1;
        if(musicWave!=null)musicWave.setActive(false);
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
            if(fullPlay!=null)fullPlay.setText("Ⅱ");
            status.setText(isMusic?"Playing music · "+(queueIndex+1)+"/"+queue.size():
                retryingSoftware?"Playing • VLC software decode":"Playing • VLC decoder");
            if(musicWave!=null&&isMusic)musicWave.invalidate();
            updateTrackButtons();
        }else if(type==MediaPlayer.Event.Paused||type==MediaPlayer.Event.Stopped||type==MediaPlayer.Event.EndReached){
            playButton.setText("▶");
            if(fullPlay!=null)fullPlay.setText("▶");
            if(type==MediaPlayer.Event.EndReached){
                status.setText("Playback finished");
                if(loopMode==LOOP_ONE){
                    ui.postDelayed(()->playMedia(false),130);
                }else if(!queue.isEmpty()&&queueIndex+1<queue.size()){
                    ui.postDelayed(()->playQueueIndex(queueIndex+1),130);
                }else if(loopMode==LOOP_ALL){
                    if(!queue.isEmpty())ui.postDelayed(()->playQueueIndex(0),130);
                    else ui.postDelayed(()->playMedia(false),130);
                }
            }
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
            originalVis.clear();
            for(int i=0;i<rootPage.getChildCount();i++){
                View child=rootPage.getChildAt(i);
                if(child!=videoBox){originalVis.put(child,child.getVisibility());child.setVisibility(View.GONE);}
            }
            rootPage.setPadding(0,0,0,0);
            rootScroll.setVerticalScrollBarEnabled(false);
            rootScroll.smoothScrollTo(0,0);
            videoBox.setClipToOutline(false);
            videoBox.setBackgroundColor(Color.BLACK);
            fullHud.setVisibility(View.VISIBLE);
            getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY|View.SYSTEM_UI_FLAG_FULLSCREEN|
                View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN|
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
            setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE);
            showFullscreenControls();
        }else{
            ui.removeCallbacks(hideFullControls);
            fullHud.animate().cancel();
            fullHud.setVisibility(View.GONE);
            fullHud.setAlpha(1f);
            for(Map.Entry<View,Integer> e:originalVis.entrySet())e.getKey().setVisibility(e.getValue());
            originalVis.clear();
            rootPage.setPadding(dp(16),dp(22),dp(16),dp(42));
            rootScroll.setVerticalScrollBarEnabled(true);
            videoBox.setBackground(round(INK,18));
            videoBox.setClipToOutline(true);
            getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR);
            setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED);
        }
        videoBox.requestLayout();
        rootPage.requestLayout();
        rootScroll.requestLayout();
    }
    @Override public void onConfigurationChanged(Configuration next){
        super.onConfigurationChanged(next);
        if(videoBox!=null)videoBox.post(()->videoBox.requestLayout());
    }
    @Override public void onBackPressed(){
        if(immersive)toggleFullscreen();
        else super.onBackPressed();
    }
    private void updateTrackButtons(){
        if(player==null)return;
        List<VlcTrackPicker.Option> subs=VlcTrackPicker.available(player,true);
        List<VlcTrackPicker.Option> audio=VlcTrackPicker.available(player,false);
        if(subtitleButton!=null){
            int count=0;for(VlcTrackPicker.Option o:subs)if(!"-1".equals(o.id))count++;
            subtitleButton.setText("CC Subtitles · "+count);
        }
        if(audioButton!=null)audioButton.setText("♫ Audio · "+audio.size());
    }
    private void applyLook(){applyLook(false);}
    private void applyLook(boolean animate){
        float k=intensity/100f;
        int mask=Color.TRANSPARENT;
        if(look==1)mask=Color.argb((int)(48*k),241,187,95);
        else if(look==2)mask=Color.argb((int)(36*k),35,213,180);
        else if(look==3)mask=Color.argb((int)(42*k),2,4,12);
        if(animate){
            final int color=mask;
            tint.animate().cancel();
            tint.animate().alpha(.1f).setDuration(130).withEndAction(()->{
                tint.setBackgroundColor(color);
                tint.animate().alpha(1f).setDuration(230)
                    .setInterpolator(new AccelerateDecelerateInterpolator()).start();
            }).start();
        }else{
            tint.setAlpha(1f);tint.setBackgroundColor(mask);
        }
        Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
        ColorMatrix m=new ColorMatrix();
        if(look==3)m.setSaturation(1f-k);
        else if(look==2)m.setSaturation(1f+.45f*k);
        else if(look==1)m.setSaturation(1f+.12f*k);
        paint.setColorFilter(new ColorMatrixColorFilter(m));
        // VLC uses TextureView (forceTextureView=true) for GPU-side color looks.
        videoLayout.setLayerType(View.LAYER_TYPE_HARDWARE,paint);
        videoLayout.setLayerPaint(paint);
        for(int i=0;i<lookButtons.size();i++){
            Button b=lookButtons.get(i);
            b.setBackground(round(i==look?INK:SOFT,16));
            b.setTextColor(i==look?Color.WHITE:INK);
            if(animate)b.animate().alpha(i==look?1f:.82f).setDuration(180).start();
            else b.setAlpha(i==look?1f:.82f);
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
