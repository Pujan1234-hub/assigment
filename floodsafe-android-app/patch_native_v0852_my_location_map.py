from pathlib import Path

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.52: My Location must visibly land on the user's GPS point in Nepal.
# Keep all river/source/alert/SATHI logic untouched.

old='    private boolean showAllStations=false;'
new='    private boolean showAllStations=false;\n    private boolean focusLocationAfterFix=false; // V0852_MY_LOCATION_FOCUS'
if old in a:
    a=a.replace(old,new,1)
elif 'V0852_MY_LOCATION_FOCUS' not in a:
    raise SystemExit('v0852 focus flag anchor missing')

old='Button locate=button(t("◎ मेरो हालको स्थान","◎ My current location")); locate.setOnClickListener(v->requestLocation()); content.addView(locate,lp(-1,dp(54),0,0,0,dp(12)));'
new='Button locate=button(t("◎ मेरो हालको स्थान","◎ My current location")); locate.setOnClickListener(v->{focusLocationAfterFix=true;requestLocation();smoothTo(mapAnchor);}); content.addView(locate,lp(-1,dp(54),0,0,0,dp(12))); // V0852_LOCATION_BUTTON'
if old in a:
    a=a.replace(old,new,1)
elif 'V0852_LOCATION_BUTTON' not in a:
    raise SystemExit('v0852 location button anchor missing')

old='''    private void requestLocation(){if(!hasLocationPermission()){requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION},REQ_LOCATION);return;}if(lm==null)return;try{Location a=lm.getLastKnownLocation(LocationManager.GPS_PROVIDER),b=lm.getLastKnownLocation(LocationManager.NETWORK_PROVIDER),best=a==null?b:b==null?a:(a.getTime()>=b.getTime()?a:b);if(best!=null&&System.currentTimeMillis()-best.getTime()<24L*60*60*1000)onLocationChanged(best);if(lm.isProviderEnabled(LocationManager.GPS_PROVIDER))lm.requestSingleUpdate(LocationManager.GPS_PROVIDER,this,getMainLooper());else if(lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER))lm.requestSingleUpdate(LocationManager.NETWORK_PROVIDER,this,getMainLooper());}catch(Exception ignored){}}'''
new='''    private void requestLocation(){
        if(!hasLocationPermission()){requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION},REQ_LOCATION);return;}
        if(lm==null)return;
        try{
            Location gps=lm.getLastKnownLocation(LocationManager.GPS_PROVIDER),net=lm.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
            Location best=gps==null?net:net==null?gps:(gps.getTime()>=net.getTime()?gps:net);
            long maxAge=focusLocationAfterFix?5L*60L*1000L:24L*60L*60L*1000L;
            if(best!=null&&System.currentTimeMillis()-best.getTime()<maxAge)onLocationChanged(best);
            // Ask BOTH providers when available. Previously GPS being enabled prevented the network fallback,
            // so indoors/weak-GPS phones could wait forever even though Android had a usable network fix.
            if(lm.isProviderEnabled(LocationManager.GPS_PROVIDER))lm.requestSingleUpdate(LocationManager.GPS_PROVIDER,this,getMainLooper());
            if(lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER))lm.requestSingleUpdate(LocationManager.NETWORK_PROVIDER,this,getMainLooper());
        }catch(Exception ignored){}
    } // V0852_DUAL_PROVIDER_LOCATION'''
if old in a:
    a=a.replace(old,new,1)
elif 'V0852_DUAL_PROVIDER_LOCATION' not in a:
    raise SystemExit('v0852 requestLocation anchor missing')

old='''place.setText(isNepal(lat,lon)?t("📍 हालको GPS • Nepal","📍 Current GPS • Nepal"):t("🌍 हालको GPS Nepal बाहिर • weather यही स्थानको हो","🌍 GPS outside Nepal • local weather only"));updateOutsideNotice();reverseGeocode();fetchWeather(lat,lon);refreshRiverUi();FloodMonitorService.startIfEnabled(this);}'''
new='''place.setText(isNepal(lat,lon)?t("📍 हालको GPS • Nepal","📍 Current GPS • Nepal"):t("🌍 हालको GPS Nepal बाहिर • weather यही स्थानको हो","🌍 GPS outside Nepal • local weather only"));updateOutsideNotice();reverseGeocode();fetchWeather(lat,lon);refreshRiverUi();if(focusLocationAfterFix){if(map!=null&&isNepal(lat,lon)){map.focusUserLocation();smoothTo(mapAnchor);}focusLocationAfterFix=false;}FloodMonitorService.startIfEnabled(this);} // V0852_FOCUS_AFTER_FIX'''
if old in a:
    a=a.replace(old,new,1)
elif 'V0852_FOCUS_AFTER_FIX' not in a:
    raise SystemExit('v0852 onLocationChanged anchor missing')

old='''void setBase(Bitmap b){base=b;invalidate();}void setStations(List<RiverStation>s,double la,double lo){data=new ArrayList<>(s);uLat=la;uLon=lo;invalidate();}void zoomBy(float f){float cx=getWidth()/2f,cy=getHeight()/2f,old=scale;scale=Math.max(1f,Math.min(6f,scale*f));float q=scale/old;tx=cx-(cx-tx)*q;ty=cy-(cy-ty)*q;invalidate();}void resetView(){scale=1f;tx=ty=0;invalidate();}void toggleTerrain(){terrain=!terrain;invalidate();}'''
new='''void setBase(Bitmap b){base=b;invalidate();}void setStations(List<RiverStation>s,double la,double lo){data=new ArrayList<>(s);uLat=la;uLon=lo;invalidate();}void zoomBy(float f){float cx=getWidth()/2f,cy=getHeight()/2f,old=scale;scale=Math.max(1f,Math.min(6f,scale*f));float q=scale/old;tx=cx-(cx-tx)*q;ty=cy-(cy-ty)*q;invalidate();}void focusUserLocation(){if(!isNepal(uLat,uLon)||getWidth()<=0||getHeight()<=0)return;float w=getWidth(),h=getHeight();scale=3.35f;float px=(float)((uLon-80)/(88.35-80))*w,py=(float)((30.5-uLat)/(30.5-26.2))*h;tx=w/2f-px*scale;ty=h/2f-py*scale;invalidate();}void resetView(){scale=1f;tx=ty=0;invalidate();}void toggleTerrain(){terrain=!terrain;invalidate();} // V0852_MAP_FOCUS_METHOD'''
if old in a:
    a=a.replace(old,new,1)
elif 'V0852_MAP_FOCUS_METHOD' not in a:
    raise SystemExit('v0852 map focus method anchor missing')

old='''if(isNepal(uLat,uLon)){float x=(float)((uLon-80)/(88.35-80))*w,y=(float)((30.5-uLat)/(30.5-26.2))*h;p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(Math.max(2f,dp(2)/scale));p.setColor(Color.rgb(11,127,208));c.drawCircle(x,y,dp(9)/scale,p);p.setStyle(Paint.Style.FILL);}'''
new='''if(isNepal(uLat,uLon)){float x=(float)((uLon-80)/(88.35-80))*w,y=(float)((30.5-uLat)/(30.5-26.2))*h;float r=dp(7)/scale;p.setStyle(Paint.Style.FILL);p.setColor(Color.WHITE);c.drawCircle(x,y,r+dp(3)/scale,p);p.setColor(Color.rgb(20,133,235));c.drawCircle(x,y,r,p);p.setColor(Color.WHITE);c.drawCircle(x,y,dp(2.2f)/scale,p);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(Math.max(1.5f,dp(2)/scale));p.setColor(Color.rgb(8,91,179));c.drawCircle(x,y,r+dp(3)/scale,p);p.setStyle(Paint.Style.FILL);} /* V0852_VISIBLE_GPS_DOT */'''
if old in a:
    a=a.replace(old,new,1)
elif 'V0852_VISIBLE_GPS_DOT' not in a:
    raise SystemExit('v0852 GPS marker anchor missing')

old='''@Override public void onRequestPermissionsResult(int code,String[]p,int[]g){super.onRequestPermissionsResult(code,p,g);if(code==REQ_LOCATION&&hasLocationPermission())requestLocation();else if(code==REQ_MIC&&checkSelfPermission(Manifest.permission.RECORD_AUDIO)==PackageManager.PERMISSION_GRANTED)showSathiDialog(null);}'''
new='''@Override public void onRequestPermissionsResult(int code,String[]p,int[]g){super.onRequestPermissionsResult(code,p,g);if(code==REQ_LOCATION){if(hasLocationPermission())requestLocation();else focusLocationAfterFix=false;}else if(code==REQ_MIC&&checkSelfPermission(Manifest.permission.RECORD_AUDIO)==PackageManager.PERMISSION_GRANTED)showSathiDialog(null);} // V0852_PERMISSION_RESULT'''
if old in a:
    a=a.replace(old,new,1)
elif 'V0852_PERMISSION_RESULT' not in a:
    raise SystemExit('v0852 permission result anchor missing')

if "versionCode 71" in g:g=g.replace("versionCode 71","versionCode 72",1)
elif "versionCode 72" not in g:raise SystemExit('v0852 versionCode anchor missing')
if "versionName '0.8.51'" in g:g=g.replace("versionName '0.8.51'","versionName '0.8.52'",1)
elif "versionName '0.8.52'" not in g:raise SystemExit('v0852 versionName anchor missing')

for marker in ['V0852_MY_LOCATION_FOCUS','V0852_LOCATION_BUTTON','V0852_DUAL_PROVIDER_LOCATION','V0852_FOCUS_AFTER_FIX','V0852_MAP_FOCUS_METHOD','V0852_VISIBLE_GPS_DOT','V0852_PERMISSION_RESULT']:
    if marker not in a:raise SystemExit('missing '+marker)

a_path.write_text(a,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.52 My Location map focus + dual-provider GPS + visible blue dot PASS')
