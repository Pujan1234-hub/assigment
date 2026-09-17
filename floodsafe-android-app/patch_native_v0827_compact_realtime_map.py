from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.27: keep the v0.8.26 native UI, but match the compact map overlay from the
# working phone screenshot, keep the map visually blue, keep geometry/stations Nepal-only,
# and make the visible counts refresh directly from the current BIPAD source.

field='    private TextView mapLiveText;'
if field not in a: raise SystemExit('v0.8.26 mapLiveText field missing')
if 'mapRainLatest' not in a:
    a=a.replace(field,field+'''\n    private volatile int mapRainLatest=-1,mapRainTotal=-1;\n    private final Runnable mapRealtimeTick=new Runnable(){@Override public void run(){\n        try{refreshRivers();refreshCompactRainCounts();}catch(Exception ignored){}\n        main.postDelayed(this,60000L);\n    }};''',1)

old_init='mapLiveText=text(t("🌊 BIPAD नदी Official Live Feed\\nOfficial feed जोडिँदैछ…","🌊 BIPAD River Official Live Feed\\nConnecting official feed…"),12,true,Color.WHITE);'
new_init='mapLiveText=text("🌊 latest official — / — • 🌧️ rain latest — / —",13,true,Color.WHITE);'
if old_init not in a: raise SystemExit('v0.8.26 live overlay init missing')
a=a.replace(old_init,new_init,1)
a=a.replace('FrameLayout.LayoutParams liveLp=new FrameLayout.LayoutParams(-1,-2,Gravity.TOP);',
            'FrameLayout.LayoutParams liveLp=new FrameLayout.LayoutParams(-2,-2,Gravity.TOP|Gravity.START);',1)
if 'mapHint=mapLiveText;\n' not in a: raise SystemExit('mapHint live overlay anchor missing')
a=a.replace('mapHint=mapLiveText;\n','mapHint=mapLiveText;\n        refreshCompactRainCounts();\n',1)

# v0.8.26 can compact onCreate onto one line, so hook the first refreshAll() itself.
refresh_anchor='refreshAll();'
if refresh_anchor not in a: raise SystemExit('refreshAll call missing')
a=a.replace(refresh_anchor,
            'refreshAll();main.removeCallbacks(mapRealtimeTick);main.postDelayed(mapRealtimeTick,60000L);',1)

us=a.find('    private void updateMapLiveOverlay(){')
ue=a.find('    private void showMapDetail(',us)
if us<0 or ue<0: raise SystemExit('updateMapLiveOverlay anchors missing')
compact=r'''    private void updateMapLiveOverlay(){
        if(mapLiveText==null)return;
        int total=0,latest=0;
        synchronized(stations){
            total=stations.size();
            for(RiverStation s:stations)if(s!=null&&s.fresh)latest++;
        }
        String rain=(mapRainLatest>=0&&mapRainTotal>=0)?(mapRainLatest+" / "+mapRainTotal):"— / —";
        mapLiveText.setText("🌊 latest official "+latest+" / "+total+" • 🌧️ rain latest "+rain);
    }

    private void refreshCompactRainCounts(){
        if(io.isShutdown())return;
        io.execute(()->{
            int latest=fetchBipadCount("rain-stations/?latest=true&limit=2000");
            int total=fetchBipadCount("rain-stations/?limit=1");
            if(latest>=0)mapRainLatest=latest;
            if(total>=0)mapRainTotal=total;
            main.post(this::updateMapLiveOverlay);
        });
    }

    private int fetchBipadCount(String path){
        HttpURLConnection c=null;
        try{
            c=(HttpURLConnection)new URL(BIPAD+path).openConnection();
            c.setConnectTimeout(12000);c.setReadTimeout(12000);
            c.setRequestProperty("Accept","application/json");
            c.setRequestProperty("User-Agent","FloodSafe-Android/0.8.27");
            int code=c.getResponseCode();if(code<200||code>=300)return -1;
            BufferedReader br=new BufferedReader(new InputStreamReader(c.getInputStream(),StandardCharsets.UTF_8));
            StringBuilder raw=new StringBuilder();String line;while((line=br.readLine())!=null)raw.append(line);br.close();
            String text=raw.toString().trim();if(text.isEmpty())return -1;
            if(text.charAt(0)=='[')return new JSONArray(text).length();
            JSONObject j=new JSONObject(text);
            if(j.has("count"))return j.optInt("count",-1);
            JSONArray rows=j.optJSONArray("results");return rows==null?-1:rows.length();
        }catch(Exception ignored){return -1;}finally{if(c!=null)c.disconnect();}
    }

'''
a=a[:us]+compact+a[ue:]

# White anchored in-map detail card. Never dim the map, never substitute another river's gauge.
ds=a.find('    private void showMapDetail(String title,String detail){')
de=a.find('    private View riskCard()',ds)
if ds<0 or de<0: raise SystemExit('showMapDetail/riskCard anchors missing')
show_station_pos=a.find('    private void showStation(RiverStation s){',ds)
if show_station_pos>0 and show_station_pos<de: de=show_station_pos
new_detail=r'''    private void showMapDetail(String title,String detail){
        if(mapDetailPanel==null)return;
        mapDetailPanel.removeAllViews();
        LinearLayout top=new LinearLayout(this);top.setOrientation(LinearLayout.HORIZONTAL);top.setGravity(Gravity.CENTER_VERTICAL);
        TextView h=text("🌊 "+(title==null?"":title),20,true,Color.rgb(16,39,70));top.addView(h,new LinearLayout.LayoutParams(0,-2,1f));
        TextView official=badge(t("आधिकारिक","OFFICIAL"),Color.rgb(230,247,255),Color.rgb(18,111,164));top.addView(official);
        TextView x=text("✕",20,true,Color.rgb(77,105,124));x.setGravity(Gravity.CENTER);x.setPadding(dp(10),dp(5),dp(4),dp(5));
        x.setOnClickListener(v->mapDetailPanel.setVisibility(View.GONE));top.addView(x);
        mapDetailPanel.addView(top);

        TextView body=text(detail==null?"":detail,13,false,Color.rgb(42,67,86));
        body.setLineSpacing(0f,1.12f);body.setPadding(dp(2),dp(10),dp(2),dp(3));mapDetailPanel.addView(body);

        TextView source=text(t("स्रोत: BIPAD / DHM official • source मा matching current gauge नभए app ले अर्को स्टेशनको data राख्दैन।",
                               "Source: BIPAD / DHM official • if no matching current gauge exists, the app does not substitute another station."),
                             11,false,Color.rgb(95,122,141));
        source.setPadding(dp(2),dp(7),dp(2),0);mapDetailPanel.addView(source);
        mapDetailPanel.setVisibility(View.VISIBLE);
    }

'''
a=a[:ds]+new_detail+a[de:]

ss=a.find('    private void showStation(RiverStation s){')
se=a.find('    private void refreshHuman()',ss)
if ss<0 or se<0: raise SystemExit('showStation anchors missing')
station=r'''    private void showStation(RiverStation s){
        if(s==null)return;
        StringBuilder b=new StringBuilder();
        if(s.district!=null&&!s.district.trim().isEmpty())b.append(t("जिल्ला: ","District: ")).append(s.district.trim()).append("\n");
        b.append(t("स्थिति: ","Status: ")).append(s.fresh?t("अहिले source मा current","current at source"):t("source मा current छैन / stale","not current at source / stale"));
        b.append("\n").append(t("अवस्था: ","Stage: ")).append(stageDot(s.stage)).append(" ").append(stageName(s.stage));
        b.append("\n").append(t("पानीको सतह: ","Water level: ")).append(Double.isFinite(s.level)?String.format(Locale.US,"%.3f m",s.level):"—");
        if(Double.isFinite(s.warning))b.append("\nWarning: ").append(String.format(Locale.US,"%.3f m",s.warning));
        if(Double.isFinite(s.danger))b.append("\nDanger: ").append(String.format(Locale.US,"%.3f m",s.danger));
        if(s.at>0)b.append("\n").append(t("पछिल्लो official update: ","Latest official update: ")).append(Instant.ofEpochMilli(s.at).atZone(ZoneId.of("Asia/Kathmandu")).toLocalDateTime());
        b.append("\n").append(t("स्रोत: BIPAD / DHM official","Source: BIPAD / DHM official"));
        showMapDetail(s.name,b.toString());
    }

'''
a=a[:ss]+station+a[se:]

# Blue geographic river network; live status colour/glow remains fresh same-river gauge only.
m=m.replace('lineColor("#7897a1"), lineWidth(1.25f), lineOpacity(0.46f)',
            'lineColor("#47d9ff"), lineWidth(1.55f), lineOpacity(0.82f)',1)
m=m.replace('lineColor("#274c56"), lineWidth(2.4f), lineOpacity(0.18f)',
            'lineColor("#0a6f92"), lineWidth(3.0f), lineOpacity(0.28f)',1)

# Tight Nepal camera target. Try known generated variants and require success below.
m=m.replace('.include(new LatLng(25.4, 79.2))\n                        .include(new LatLng(31.15, 89.15)).build();',
            '.include(new LatLng(26.2, 80.0))\n                        .include(new LatLng(30.5, 88.35)).build();',1)
m=m.replace('.include(new LatLng(25.8, 79.6))\n                        .include(new LatLng(30.8, 88.7)).build();',
            '.include(new LatLng(26.2, 80.0))\n                        .include(new LatLng(30.5, 88.35)).build();',1)

g=g.replace('versionCode 46','versionCode 47',1).replace("versionName '0.8.26'","versionName '0.8.27'",1)
if 'versionCode 47' not in g or "versionName '0.8.27'" not in g: raise SystemExit('v0.8.27 version bump failed')

for marker in ['viewportInsideNepalStrict(fw,fs,fe,fn,nepal)','clipWaysToNepalDense(candidates,nepal)','currentFlowRivers','routeD<=0.75','RiverTapInfo']:
    if marker not in m: raise SystemExit('map truth marker missing: '+marker)
for marker in ['latest official "+latest+" / "+total','refreshCompactRainCounts','source मा matching current gauge नभए','main.postDelayed(mapRealtimeTick,60000L)']:
    if marker not in a: raise SystemExit('activity realtime marker missing: '+marker)
if 'BIPAD नदी Official Live Feed' in a: raise SystemExit('large BIPAD live-feed panel remained')
if 'List<RiverWay> visibleSnapshot=new ArrayList<>(rivers);' in m: raise SystemExit('fake all-river flow animation remained')

m_path.write_text(m,encoding='utf-8')
a_path.write_text(a,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.27 compact realtime Nepal-only river map PASS')
