from pathlib import Path
p=Path('vault-android/app/src/main/java/com/pjbuilts/vault/MainActivity.java')
s=p.read_text()
def sub(a,b):
 global s
 if a not in s: raise RuntimeError("Missing fragment: "+a[:95])
 s=s.replace(a,b,1)
sub('import android.os.Bundle;','import android.os.Bundle;\nimport android.os.SystemClock;\nimport android.widget.FrameLayout;\nimport android.view.animation.DecelerateInterpolator;')
sub('    private boolean currentLocked=true;','''    private boolean currentLocked=true, fromResume=false;
    private long awayAt=-1L;
    private static final long QUICK_SWITCH=120000L;
    private FrameLayout curtain=null;
    private String screen="dashboard";
    private String savedProject=null,savedName=null,savedTab="credentials";''')
sub('''        store=new VaultStore(this);
        drawLocked();
    }''','''        store=new VaultStore(this);
        if(b!=null){savedProject=b.getString("project");savedName=b.getString("projectName");
            savedTab=b.getString("tab","credentials");}
        drawLocked();
        if(store.isInitialized()&&store.hasBiometric())
            handler.postDelayed(()->{if(!isFinishing())bioOnly(false);},200);
    }
    @Override protected void onSaveInstanceState(Bundle b){
        b.putString("project",currentProject);b.putString("projectName",currentProjectName);
        b.putString("tab",currentTab);super.onSaveInstanceState(b);
    }''')
start=s.index('    @Override public void onStop(){')
end=s.index('    private int d(float v)',start)
s=s[:start]+'''    @Override public void onPause(){
        if(store!=null && store.isUnlocked()&&!filePicker&&!biometricPending)
            awayAt=SystemClock.elapsedRealtime();
        super.onPause();
    }
    @Override public void onStop(){super.onStop();}
    @Override public void onResume(){
        super.onResume();
        if(store==null||filePicker||biometricPending||currentLocked)return;
        if(store.isUnlocked()&&awayAt>0){
            long elapsed=SystemClock.elapsedRealtime()-awayAt;awayAt=-1;
            if(elapsed>=QUICK_SWITCH){
                store.lock();coverScreen();handler.postDelayed(()->bioOnly(true),100);
            }
        }else if(!store.isUnlocked()){
            coverScreen();handler.postDelayed(()->bioOnly(true),100);
        }
    }
    @Override protected void onDestroy(){if(store!=null)store.lock();super.onDestroy();}
    @Override public void onBackPressed(){
        if(curtain!=null||biometricPending)return;
        if(store==null||!store.isUnlocked()){super.onBackPressed();return;}
        if("editor".equals(screen)||"detail".equals(screen)){drawProject();}
        else if("project".equals(screen)){drawDashboard();}
        else moveTaskToBack(true);
    }
    private void coverScreen(){
        if(curtain!=null)return;
        curtain=new FrameLayout(this);curtain.setBackgroundColor(CREAM);curtain.setClickable(true);
        LinearLayout pane=linear(true);pane.setGravity(Gravity.CENTER);
        padding(pane,25,25,25,25);
        ImageView icon=new ImageView(this);icon.setImageResource(R.drawable.vault_launcher);
        pane.addView(icon,lp(96,96));gap(pane,20);
        TextView h=text("VAULT LOCKED",25,NAVY,true);h.setGravity(Gravity.CENTER);pane.addView(h);gap(pane,9);
        TextView caption=text("Fingerprint unlock • Your workspace stays in place",13,GOLD,false);
        caption.setGravity(Gravity.CENTER);pane.addView(caption);gap(pane,25);
        TextView retry=button("◎   UNLOCK WITH FINGERPRINT",true);pane.addView(retry,lp(-1,54));
        retry.setOnClickListener(v->bioOnly(true));
        curtain.addView(pane,new FrameLayout.LayoutParams(-1,-1));
        getWindow().addContentView(curtain,new android.view.ViewGroup.LayoutParams(-1,-1));
    }
    private void uncover(){
        if(curtain==null)return;
        android.view.ViewParent parent=curtain.getParent();
        if(parent instanceof android.view.ViewGroup)((android.view.ViewGroup)parent).removeView(curtain);
        curtain=null;awayAt=-1;
    }
    private void bioOnly(boolean resume){
        if(store==null||biometricPending||!store.hasBiometric())return;
        fromResume=resume;
        if(!canBiometric()){toast("Strong biometric not available; use PIN recovery");return;}
        try{showBiometric("Unlock PJBUILTS Vault",store.biometricUnlockCipher(),false);}
        catch(Exception e){toast("Biometric unavailable: "+e.getMessage());}
    }
''' + s[end:]
sub('''        currentLocked=true;currentProject=null;''','''        currentLocked=true;''')
sub('''        } else {
            TextView steps=text("STEP 1 / 2   PRIVATE PIN     →     STRONG BIOMETRIC",11,GOLD,true);
            steps.setGravity(Gravity.CENTER);pane.addView(steps);gap(pane,12);
            TextView pin=button("⌑   VERIFY VAULT PIN   ›",true);pane.addView(pin,lp(-1,54));pin.setOnClickListener(v->promptPin());
        }''','''        } else if(store.hasBiometric()){
            TextView tag=text("PRIVATE WORKSPACE  /  QUICK ACCESS",11,GOLD,true);
            tag.setGravity(Gravity.CENTER);pane.addView(tag);gap(pane,13);
            TextView bio=button("◎   UNLOCK WITH FINGERPRINT   ›",true);
            pane.addView(bio,lp(-1,54));bio.setOnClickListener(v->bioOnly(false));gap(pane,12);
            TextView recovery=text("Fingerprint unavailable? Recover using your Vault PIN",12,MUTED,false);
            recovery.setGravity(Gravity.CENTER);pane.addView(recovery);
            recovery.setOnClickListener(v->new AlertDialog.Builder(this).setTitle("PIN recovery")
                .setMessage("Use only if your biometrics have changed; strong biometric will be required again.")
                .setNegativeButton("CANCEL",null).setPositiveButton("RECOVER",(d,w)->promptPin()).show());
        }else{
            TextView setup=button("⌑   FINISH FINGERPRINT SETUP WITH PIN",true);
            pane.addView(setup,lp(-1,54));setup.setOnClickListener(v->promptPin());
        }''')
sub('''        TextView lock=iconBtn("⌁",v->{store.lock();currentProject=null;drawLocked();});''','''        TextView lock=iconBtn("⌁",v->{store.lock();drawLocked();});''')
sub('''                .setSubtitle("Both Vault PIN and strong biometric are required")''','''                .setSubtitle(enrolling?"First-time setup":"Fingerprint quick access")''')
sub('''                    biometricPending=false;store.lock();drawLocked();
                }).build();''','''                    biometricPending=false;store.lock();if(curtain==null)drawLocked();
                }).build();''')
sub('''                        if(!store.isUnlocked())throw new SecurityException("Vault locked");
                        drawDashboard();toast("Two-step verification successful");
                    }catch(Exception e){store.lock();drawLocked();toast("Biometric failed: "+e.getMessage());}''','''                        if(!store.isUnlocked())throw new SecurityException("Vault locked");
                        if(fromResume&&curtain!=null)uncover();
                        else{uncover();restorePage();}
                    }catch(Exception e){store.lock();if(curtain==null)drawLocked();toast("Biometric failed: "+e.getMessage());}''')
sub('''                    store.lock();drawLocked();
                    if(code!=BiometricPrompt.BIOMETRIC_ERROR_USER_CANCELED)toast(message.toString());''','''                    store.lock();if(curtain==null)drawLocked();
                    if(code!=BiometricPrompt.BIOMETRIC_ERROR_USER_CANCELED)toast(message.toString());''')
sub('''        }catch(Exception e){biometricPending=false;store.lock();drawLocked();toast("Biometric unavailable: "+e.getMessage());}
    }

    private void drawDashboard(){if(!store.isUnlocked()){drawLocked();return;}currentProject=null;page();brandHeader(false);''','''        }catch(Exception e){biometricPending=false;store.lock();if(curtain==null)drawLocked();toast("Biometric unavailable: "+e.getMessage());}
    }
    private void restorePage(){
        if(savedProject!=null){currentProject=savedProject;currentProjectName=savedName;
           currentTab=savedTab;savedProject=null;}
        if(currentProject!=null&&currentProjectName!=null)drawProject();else drawDashboard();
    }
    private void drawDashboard(){if(!store.isUnlocked()){drawLocked();return;}
        screen="dashboard";currentProject=null;page();brandHeader(false);''')
sub('''    private void drawProject(){if(!store.isUnlocked()){drawLocked();return;}page();brandHeader(true);''','''    private void drawProject(){if(!store.isUnlocked()){drawLocked();return;}
        screen="project";page();brandHeader(true);''')
sub('''    private void credentialForm(JSONObject old){
        if(!store.isUnlocked()){drawLocked();return;}''','''    private void credentialForm(JSONObject old){
        if(!store.isUnlocked()){drawLocked();return;}screen="editor";''')
sub('''    private void credentialDetail(JSONObject o){
        LinearLayout content''','''    private void credentialDetail(JSONObject o){
        screen="detail";
        LinearLayout content''')
sub('''        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setClipToPadding(false);''','''        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setClipToPadding(false);''')
sub('''        setContentView(scroll);
    }
    private void brandHeader''','''        scroll.setAlpha(.96f);
        scroll.animate().alpha(1f).setDuration(150).setInterpolator(new DecelerateInterpolator()).start();
        setContentView(scroll);
    }
    private void brandHeader''')
# Quick tech aesthetic with an actual functional session badge.
needle='''            root.addView(status);gap(root,24);'''
if needle in s:
 s=s.replace(needle,'''            root.addView(status);gap(root,15);
            LinearLayout quick=card();quick.addView(text("◈  DEV QUICK SWITCH / SESSION ACTIVE",11,GOLD,true));gap(quick,8);
            quick.addView(text("Copy, paste, switch apps and return right here.",13,NAVY,false));gap(quick,6);
            quick.addView(text("02:00 GRACE  /  FINGERPRINT AFTER TIMEOUT",10,MUTED,true));root.addView(quick);gap(root,22);''',1)
sub('''        content.addView(text("USERNAME / PROJECT ID",11,GOLD,true));TextView username=text(o.optString("username"),15,NAVY,true);content.addView(username);gap(content,13);''','''        content.addView(text("USERNAME / PROJECT ID",11,GOLD,true));TextView username=text(o.optString("username"),15,NAVY,true);content.addView(username);
        TextView copyId=button("COPY USERNAME",false);content.addView(copyId,lp(-1,41));
        copyId.setOnClickListener(v->copySecret(o.optString("username")));gap(content,13);''')
p.write_text(s)
b=Path('vault-android/app/build.gradle')
t=b.read_text().replace("applicationId 'com.pjbuilts.vault.secure2fa.premium'","applicationId 'com.pjbuilts.vault.quickvault23'")
t=t.replace("versionCode 3","versionCode 4").replace("versionName '2.2.0-premium'","versionName '2.3.0-quickaccess'")
b.write_text(t)
print("Quick-access patch applied")
