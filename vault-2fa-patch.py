from pathlib import Path
p=Path('vault-android/app/src/main/java/com/pjbuilts/vault/MainActivity.java')
s=p.read_text()
def sub(a,b):
 global s
 if a not in s: raise RuntimeError('Missing expected source fragment: '+a[:35])
 s=s.replace(a,b)
sub('''            if(store.hasBiometric()){
                TextView biometric=button("◎   UNLOCK WITH BIOMETRICS   ›",true);pane.addView(biometric,lp(-1,54));biometric.setOnClickListener(v->biometricUnlock());gap(pane,12);
            }
            TextView pin=button("⌑   UNLOCK WITH VAULT PIN",!store.hasBiometric());pane.addView(pin,lp(-1,52));pin.setOnClickListener(v->promptPin());''','''            TextView steps=text("STEP 1 / 2   PRIVATE PIN     →     STRONG BIOMETRIC",11,GOLD,true);
            steps.setGravity(Gravity.CENTER);pane.addView(steps);gap(pane,12);
            TextView pin=button("⌑   VERIFY VAULT PIN   ›",true);pane.addView(pin,lp(-1,54));pin.setOnClickListener(v->promptPin());''')
sub('dialog.dismiss();drawDashboard();promptEnableBiometric();','dialog.dismiss();requireBiometricEnrollment();')
sub('dlg.dismiss();drawDashboard();','dlg.dismiss();finishPinStep();')
start=s.index('    private void promptEnableBiometric(){')
end=s.index('    private void drawDashboard(){',start)
new='''    // Both steps are mandatory. PIN does not grant access to the UI.
    private void finishPinStep(){
        if(!canBiometric()){
            store.lock();drawLocked();toast("Strong fingerprint needed. Add it in Android Settings first.");return;
        }
        if(!store.hasBiometric()){requireBiometricEnrollment();return;}
        try {showBiometric("Step 2/2 • Fingerprint / strong face",store.biometricUnlockCipher(),false);}
        catch(Exception e){store.lock();drawLocked();toast("Biometric failed: "+e.getMessage());}
    }
    private void requireBiometricEnrollment(){
        if(!canBiometric()){
            store.lock();drawLocked();toast("Enroll a strong fingerprint in Android Settings first.");return;
        }
        new AlertDialog.Builder(this).setTitle("Enable required biometric verification")
            .setMessage("Unlock requires BOTH your separate Vault PIN and a strong fingerprint or strong face. Pattern is not accepted.")
            .setCancelable(false)
            .setNegativeButton("LOCK VAULT",(dialog,which)->{store.lock();drawLocked();})
            .setPositiveButton("VERIFY FINGERPRINT",(dialog,which)->{
                try{showBiometric("Enrol step 2/2 • Strong biometric",store.newBiometricEnableCipher(),true);}
                catch(Exception e){store.lock();drawLocked();toast("Biometric setup failed: "+e.getMessage());}
            }).show();
    }
    private void promptEnableBiometric(){requireBiometricEnrollment();}
    private void showBiometric(String title,Cipher cipher,boolean enrolling){
        biometricPending=true;
        Executor executor=getMainExecutor();
        try{
            BiometricPrompt prompt=new BiometricPrompt.Builder(this).setTitle(title)
                .setSubtitle("Both Vault PIN and strong biometric are required")
                .setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_STRONG)
                .setNegativeButton("Cancel • Lock Vault",executor,(dialog,which)->{
                    biometricPending=false;store.lock();drawLocked();
                }).build();
            prompt.authenticate(new BiometricPrompt.CryptoObject(cipher),new CancellationSignal(),executor,new BiometricPrompt.AuthenticationCallback(){
                @Override public void onAuthenticationSucceeded(BiometricPrompt.AuthenticationResult result){
                    super.onAuthenticationSucceeded(result);biometricPending=false;
                    try{
                        if(result.getCryptoObject()==null||result.getCryptoObject().getCipher()==null)
                            throw new SecurityException("Missing biometric crypto proof");
                        if(enrolling)store.completeBiometricEnable(result.getCryptoObject().getCipher());
                        else store.completeBiometricUnlock(result.getCryptoObject().getCipher());
                        if(!store.isUnlocked())throw new SecurityException("Vault locked");
                        drawDashboard();toast("Two-step verification successful");
                    }catch(Exception e){store.lock();drawLocked();toast("Biometric failed: "+e.getMessage());}
                }
                @Override public void onAuthenticationError(int code,CharSequence message){
                    super.onAuthenticationError(code,message);biometricPending=false;
                    store.lock();drawLocked();
                    if(code!=BiometricPrompt.BIOMETRIC_ERROR_USER_CANCELED)toast(message.toString());
                }
            });
        }catch(Exception e){biometricPending=false;store.lock();drawLocked();toast("Biometric unavailable: "+e.getMessage());}
    }

'''
s=s[:start]+new+s[end:]
sub('''        TextView bio=button(store.hasBiometric()?"DISABLE BIOMETRICS":"ENABLE BIOMETRICS",false);box.addView(bio,lp(-1,49));
        update.setOnClickListener(v->changePinForm());bio.setOnClickListener(v->{if(store.hasBiometric()){
            store.disableBiometric();toast("Biometric access disabled");}else promptEnableBiometric();});''','''        TextView bio=button(store.hasBiometric()?"STRONG BIOMETRIC REQUIRED • ACTIVE":"ENROLL STRONG BIOMETRIC",false);box.addView(bio,lp(-1,49));
        update.setOnClickListener(v->changePinForm());bio.setOnClickListener(v->{
            if(store.hasBiometric())toast("Biometric remains required for every unlock.");
            else requireBiometricEnrollment();
        });''')
p.write_text(s)
p=Path('vault-android/app/build.gradle')
s=p.read_text().replace("applicationId 'com.pjbuilts.vault.secure'","applicationId 'com.pjbuilts.vault.secure2fa'")
s=s.replace('versionCode 1','versionCode 2').replace("versionName '2.0.0-secure'","versionName '2.1.0-2fa'")
p.write_text(s)
p=Path('vault-android/app/src/main/AndroidManifest.xml')
s=p.read_text().replace('<manifest xmlns:android="http://schemas.android.com/apk/res/android">','<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n    <uses-permission android:name="android.permission.USE_BIOMETRIC"/>')
p.write_text(s.replace('android:label="PJBUILTS Vault"','android:label="@string/app_name"'))
p=Path('vault-android/app/src/main/res/values/strings.xml')
p.write_text('<resources><string name="app_name">PJBUILTS Vault 2FA</string></resources>\n')
print('Patched mandatory 2-step PIN + strong biometric unlock')
