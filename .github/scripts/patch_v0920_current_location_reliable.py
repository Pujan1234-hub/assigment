from pathlib import Path

p = Path('floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java')
s = p.read_text(encoding='utf-8')

old = '''    private void requestLocation(){if(!hasLocationPermission()){requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION},REQ_LOCATION);return;}if(lm==null)return;try{Location a=lm.getLastKnownLocation(LocationManager.GPS_PROVIDER),b=lm.getLastKnownLocation(LocationManager.NETWORK_PROVIDER),best=a==null?b:b==null?a:(a.getTime()>=b.getTime()?a:b);if(best!=null&&System.currentTimeMillis()-best.getTime()<24L*60*60*1000)onLocationChanged(best);if(lm.isProviderEnabled(LocationManager.GPS_PROVIDER))lm.requestSingleUpdate(LocationManager.GPS_PROVIDER,this,getMainLooper());else if(lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER))lm.requestSingleUpdate(LocationManager.NETWORK_PROVIDER,this,getMainLooper());}catch(Exception ignored){}}
'''

new = '''    private void requestLocation(){
        if(!hasLocationPermission()){
            requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION},REQ_LOCATION);
            return;
        }
        if(lm==null)return;
        final long now=System.currentTimeMillis();
        Location best=null;
        for(String provider:new String[]{LocationManager.GPS_PROVIDER,LocationManager.NETWORK_PROVIDER,LocationManager.PASSIVE_PROVIDER}){
            try{
                Location candidate=lm.getLastKnownLocation(provider);
                if(candidate==null)continue;
                double a=candidate.getLatitude(),o=candidate.getLongitude();
                if(!Double.isFinite(a)||!Double.isFinite(o)||a<-90d||a>90d||o<-180d||o>180d)continue;
                if(best==null||candidate.getTime()>best.getTime())best=candidate;
            }catch(SecurityException|IllegalArgumentException ignored){}
        }
        if(best!=null){
            long at=best.getTime()>0L?best.getTime():now;
            long age=now-at;
            if(age>=-5L*60L*1000L&&age<24L*60L*60L*1000L)onLocationChanged(best);
        }

        // Ask BOTH network and GPS. Previously GPS won the if/else and indoors it could wait
        // forever even though the network provider already knew the current location.
        for(String provider:new String[]{LocationManager.NETWORK_PROVIDER,LocationManager.GPS_PROVIDER}){
            try{
                if(!lm.isProviderEnabled(provider))continue;
                if(Build.VERSION.SDK_INT>=30){
                    lm.getCurrentLocation(provider,null,getMainExecutor(),location->{if(location!=null)onLocationChanged(location);});
                }else{
                    lm.requestSingleUpdate(provider,this,getMainLooper());
                }
            }catch(SecurityException|IllegalArgumentException ignored){}
        }
    }
'''

if old not in s:
    raise SystemExit('requestLocation exact baseline not found; refusing broad edit')
s = s.replace(old, new, 1)

resume_anchor = '    @Override protected void onNewIntent(Intent i){super.onNewIntent(i);setIntent(i);consumeSathiIntent(i);}\n'
resume_add = resume_anchor + '    @Override protected void onResume(){super.onResume();if(hasLocationPermission())requestLocation();} // V0920_CURRENT_LOCATION_RETRY\n'
if 'V0920_CURRENT_LOCATION_RETRY' not in s:
    if resume_anchor not in s:
        raise SystemExit('onNewIntent anchor not found; refusing broad edit')
    s = s.replace(resume_anchor, resume_add, 1)

p.write_text(s, encoding='utf-8')
print('V0920_CURRENT_LOCATION_RELIABLE_OK')
