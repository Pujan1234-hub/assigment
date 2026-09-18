from pathlib import Path

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.52: My Location must visibly land on the user's real GPS point on the
# ACTUAL MapLibre map used by the app. Keep river/source/alert/SATHI logic untouched.

old='    private boolean showAllStations=false;'
new='    private boolean showAllStations=false;\n    private boolean focusLocationAfterFix=false; // V0852_MY_LOCATION_FOCUS'
if old in a:
    a=a.replace(old,new,1)
elif 'V0852_MY_LOCATION_FOCUS' not in a:
    raise SystemExit('v0852 focus flag anchor missing')

old='Button locate=button(t("◎ मेरो हालको स्थान","◎ My current location")); locate.setOnClickListener(v->requestLocation()); content.addView(locate,lp(-1,dp(54),0,0,0,dp(12)));'
new='Button locate=button(t("◎ मेरो हालको स्थान","◎ My current location")); locate.setOnClickListener(v->{focusLocationAfterFix=true;place.setText(t("📍 हालको स्थान खोज्दै…","📍 Finding current location…"));requestLocation();smoothTo(mapAnchor);}); content.addView(locate,lp(-1,dp(54),0,0,0,dp(12))); // V0852_LOCATION_BUTTON'
if old in a:
    a=a.replace(old,new,1)
elif 'V0852_LOCATION_BUTTON' not in a:
    raise SystemExit('v0852 location button anchor missing')

old='''    private void requestLocation(){if(!hasLocationPermission()){requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION},REQ_LOCATION);return;}if(lm==null)return;try{Location a=lm.getLastKnownLocation(LocationManager.GPS_PROVIDER),b=lm.getLastKnownLocation(LocationManager.NETWORK_PROVIDER),best=a==null?b:b==null?a:(a.getTime()>=b.getTime()?a:b);if(best!=null&&System.currentTimeMillis()-best.getTime()<24L*60*60*1000)onLocationChanged(best);if(lm.isProviderEnabled(LocationManager.GPS_PROVIDER))lm.requestSingleUpdate(LocationManager.GPS_PROVIDER,this,getMainLooper());else if(lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER))lm.requestSingleUpdate(LocationManager.NETWORK_PROVIDER,this,getMainLooper());}catch(Exception ignored){}}'''
new='''    private void requestLocation(){
        if(!hasLocationPermission()){requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION},REQ_LOCATION);return;}
        if(lm==null)return;
        final boolean explicit=focusLocationAfterFix;
        try{
            Location gps=lm.getLastKnownLocation(LocationManager.GPS_PROVIDER),net=lm.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
            Location best=gps==null?net:net==null?gps:(gps.getTime()>=net.getTime()?gps:net);
            long maxAge=explicit?5L*60L*1000L:24L*60L*60L*1000L;
            if(best!=null&&System.currentTimeMillis()-best.getTime()<maxAge)onLocationChanged(best);
            boolean gpsOn=lm.isProviderEnabled(LocationManager.GPS_PROVIDER),netOn=lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER);
            if(!gpsOn&&!netOn){
                if(explicit){focusLocationAfterFix=false;new AlertDialog.Builder(this).setTitle(t("Location बन्द छ","Location is off")).setMessage(t("हालको स्थान देखाउन फोनको Location/GPS खोल्नुहोस्।","Turn on phone Location/GPS to show your current point on the map.")).setNegativeButton(t("रद्द","Cancel"),null).setPositiveButton(t("Location खोल्नुहोस्","Open location settings"),(d,w)->{try{startActivity(new Intent(android.provider.Settings.ACTION_LOCATION_SOURCE_SETTINGS));}catch(Exception ignored){}}).show();}
                return;
            }
            if(explicit){
                // Keep both providers alive briefly so weak-GPS/indoor phones can still get a network fix.
                if(gpsOn)lm.requestLocationUpdates(LocationManager.GPS_PROVIDER,0L,0f,this,getMainLooper());
                if(netOn)lm.requestLocationUpdates(LocationManager.NETWORK_PROVIDER,0L,0f,this,getMainLooper());
                main.postDelayed(()->{try{lm.removeUpdates(this);}catch(Exception ignored){}if(focusLocationAfterFix){focusLocationAfterFix=false;android.widget.Toast.makeText(this,t("Location भेटिएन — GPS on गरेर फेरि try गर्नुहोस्","Location not found — turn GPS on and try again"),android.widget.Toast.LENGTH_LONG).show();}},15000L);
            }else{
                if(gpsOn)lm.requestSingleUpdate(LocationManager.GPS_PROVIDER,this,getMainLooper());
                if(netOn)lm.requestSingleUpdate(LocationManager.NETWORK_PROVIDER,this,getMainLooper());
            }
        }catch(Exception ignored){}
    } // V0852_DUAL_PROVIDER_LOCATION'''
if old in a:
    a=a.replace(old,new,1)
elif 'V0852_DUAL_PROVIDER_LOCATION' not in a:
    raise SystemExit('v0852 requestLocation anchor missing')

old='''place.setText(isNepal(lat,lon)?t("📍 हालको GPS • Nepal","📍 Current GPS • Nepal"):t("🌍 हालको GPS Nepal बाहिर • weather यही स्थानको हो","🌍 GPS outside Nepal • local weather only"));updateOutsideNotice();reverseGeocode();fetchWeather(lat,lon);refreshRiverUi();FloodMonitorService.startIfEnabled(this);}'''
new='''boolean focusNow=focusLocationAfterFix;if(map!=null)map.setUserLocation(lat,lon,focusNow);place.setText(isNepal(lat,lon)?t("📍 हालको GPS • Nepal","📍 Current GPS • Nepal"):t("🌍 हालको GPS Nepal बाहिर • weather यही स्थानको हो","🌍 GPS outside Nepal • local weather only"));updateOutsideNotice();reverseGeocode();fetchWeather(lat,lon);refreshRiverUi();if(focusNow&&isNepal(lat,lon)){smoothTo(mapAnchor);}focusLocationAfterFix=false;FloodMonitorService.startIfEnabled(this);} // V0852_FOCUS_AFTER_FIX'''
if old in a:
    a=a.replace(old,new,1)
elif 'V0852_FOCUS_AFTER_FIX' not in a:
    raise SystemExit('v0852 onLocationChanged anchor missing')

# Patch the real MapLibre map view, not the old legacy Canvas map.
if 'V0852_MAPLIBRE_USER_LOCATION' not in m:
    anchor='    void zoomBy(float factor) {'
    if anchor not in m: raise SystemExit('v0852 MapLibre zoom anchor missing')
    methods='''    void setUserLocation(double lat, double lon, boolean focus) {\n        userLat = lat;\n        userLon = lon;\n        refreshUserSource();\n        if (focus) focusUserLocation();\n    } // V0852_MAPLIBRE_USER_LOCATION\n\n    void focusUserLocation() {\n        if (!Double.isFinite(userLat) || !Double.isFinite(userLon) || !isNepalish(userLat, userLon)) return;\n        if (map == null || !styleReady) { main.postDelayed(this::focusUserLocation, 250L); return; }\n        CameraPosition old = map.getCameraPosition();\n        double targetZoom = old.zoom < 9.0 ? 12.2 : Math.max(10.0, Math.min(15.0, old.zoom));\n        CameraPosition cp = new CameraPosition.Builder(old).target(new LatLng(userLat, userLon)).zoom(targetZoom).tilt(terrain ? 35.0 : 0.0).bearing(0.0).build();\n        refreshUserSource();\n        map.animateCamera(CameraUpdateFactory.newCameraPosition(cp), 650);\n    } // V0852_MAP_FOCUS_METHOD\n\n'''
    m=m.replace(anchor,methods+anchor,1)

# Make the current-location point unmistakable and keep it above station layers.
old_halo='circleColor("#ffffff"), circleRadius(9.0f), circleOpacity(0.72f))'
new_halo='circleColor("#ffffff"), circleRadius(13.0f), circleOpacity(0.82f)) // V0852_VISIBLE_GPS_DOT'
if old_halo in m:
    m=m.replace(old_halo,new_halo,1)
elif 'V0852_VISIBLE_GPS_DOT' not in m:
    raise SystemExit('v0852 user halo anchor missing')
old_dot='circleColor("#0b7fd0"), circleRadius(5.7f), circleStrokeColor("#ffffff"), circleStrokeWidth(1.5f))'
new_dot='circleColor("#0b7fd0"), circleRadius(7.5f), circleStrokeColor("#ffffff"), circleStrokeWidth(2.4f))'
if old_dot in m:
    m=m.replace(old_dot,new_dot,1)
elif 'circleRadius(7.5f)' not in m:
    raise SystemExit('v0852 user dot anchor missing')

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

for marker in ['V0852_MY_LOCATION_FOCUS','V0852_LOCATION_BUTTON','V0852_DUAL_PROVIDER_LOCATION','V0852_FOCUS_AFTER_FIX','V0852_PERMISSION_RESULT']:
    if marker not in a:raise SystemExit('missing activity '+marker)
for marker in ['V0852_MAPLIBRE_USER_LOCATION','V0852_MAP_FOCUS_METHOD','V0852_VISIBLE_GPS_DOT']:
    if marker not in m:raise SystemExit('missing map '+marker)

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.52 REAL MapLibre My Location + dual-provider GPS + visible blue dot PASS')
