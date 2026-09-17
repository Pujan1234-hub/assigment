from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.26 field fix: make the native map match the proven video/web interaction
# while preserving all v0.8.25 source-truth, Nepal clipping, current-only flow and alerts.

# Let river taps travel back to the Activity instead of opening a dimmed AlertDialog.
tap_anchor='interface StationTapListener { void onStationTap(Object stationObject); }'
if tap_anchor not in m:
    raise SystemExit('StationTapListener anchor missing')
if 'static final class RiverTapInfo' not in m:
    m=m.replace(tap_anchor,tap_anchor+'''
    static final class RiverTapInfo {
        final String title, detail;
        RiverTapInfo(String t,String d){title=t;detail=d;}
    }''',1)

old_alert='new AlertDialog.Builder(getContext()).setTitle(title).setMessage(x.toString()).setPositiveButton("ठीक छ",null).show();'
new_alert='if(stationTapListener!=null){stationTapListener.onStationTap(new RiverTapInfo(title,x.toString()));return;} new AlertDialog.Builder(getContext()).setTitle(title).setMessage(x.toString()).setPositiveButton("ठीक छ",null).show();'
if old_alert not in m:
    raise SystemExit('river AlertDialog anchor missing')
m=m.replace(old_alert,new_alert,1)

# Activity fields used by the video-style map overlays.
field_anchor='private FloodSafeNativeMapView map;'
if field_anchor not in a:
    raise SystemExit('FloodSafeNativeMapView field anchor missing')
if 'private FrameLayout mapHolder;' not in a:
    a=a.replace(field_anchor,field_anchor+'''
    private FrameLayout mapHolder;
    private LinearLayout mapDetailPanel;
    private TextView mapLiveText;''',1)

# Replace the compact card with the layout shown in the supplied video:
# 2x2 controls, close strip, tall satellite map, black BIPAD live overlay,
# right-side +/- buttons and a white in-map detail card.
start=a.find('    private View mapCard(){')
end=a.find('    private View riskCard()',start)
if start<0 or end<0:
    raise SystemExit('mapCard anchors missing')
map_card=r'''    private View mapCard(){
        LinearLayout c=card();

        LinearLayout head=new LinearLayout(this);head.setOrientation(LinearLayout.HORIZONTAL);head.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout labels=new LinearLayout(this);labels.setOrientation(LinearLayout.VERTICAL);
        head.addView(labels,new LinearLayout.LayoutParams(0,-2,1f));
        mapTitle=text("",22,true,Color.rgb(16,39,70));mapSub=text("",12,true,Color.rgb(92,123,146));
        labels.addView(mapTitle);labels.addView(mapSub,lp(-1,-2,0,dp(3),0,0));
        TextView live=badge(t("मापन उपलब्ध","MEASUREMENTS LIVE"),Color.rgb(232,255,243),Color.rgb(18,128,90));head.addView(live);
        c.addView(head);

        LinearLayout tools1=new LinearLayout(this);tools1.setOrientation(LinearLayout.HORIZONTAL);
        Button zi=smallButton("＋ "+t("ठूलो बनाउनुहोस्","Zoom in"));
        Button zo=smallButton("− "+t("सानो बनाउनुहोस्","Zoom out"));
        tools1.addView(zi,weight());tools1.addView(zo,weight());
        c.addView(tools1,lp(-1,dp(54),0,dp(12),0,dp(6)));

        LinearLayout tools2=new LinearLayout(this);tools2.setOrientation(LinearLayout.HORIZONTAL);
        Button d3=smallButton("◇ "+t("3D भू-आकृति","3D terrain"));
        Button reset=smallButton("🇳🇵 "+t("नेपाल","Nepal"));
        tools2.addView(d3,weight());tools2.addView(reset,weight());
        c.addView(tools2,lp(-1,dp(54),0,0,0,dp(10)));

        Button close=smallButton("✕ "+t("नदी नक्सा बन्द गर्नुहोस्","Close river map"));
        c.addView(close,lp(-1,dp(52),0,0,0,dp(10)));

        mapHolder=new FrameLayout(this);
        mapHolder.setBackground(round(Color.rgb(8,24,34),20,Color.rgb(204,224,235),1));

        map=new FloodSafeNativeMapView(this,obj->{
            if(obj instanceof RiverStation)showStation((RiverStation)obj);
            else if(obj instanceof FloodSafeNativeMapView.RiverTapInfo){
                FloodSafeNativeMapView.RiverTapInfo info=(FloodSafeNativeMapView.RiverTapInfo)obj;
                showMapDetail(info.title,info.detail);
            }
        });
        mapHolder.addView(map,new FrameLayout.LayoutParams(-1,-1));

        mapLiveText=text(t("🌊 BIPAD नदी Official Live Feed\nOfficial feed जोडिँदैछ…","🌊 BIPAD River Official Live Feed\nConnecting official feed…"),12,true,Color.WHITE);
        mapLiveText.setPadding(dp(13),dp(11),dp(13),dp(11));
        mapLiveText.setBackground(round(Color.argb(226,5,28,41),18,Color.argb(150,126,201,230),1));
        FrameLayout.LayoutParams liveLp=new FrameLayout.LayoutParams(-1,-2,Gravity.TOP);
        liveLp.setMargins(dp(12),dp(12),dp(68),0);
        mapHolder.addView(mapLiveText,liveLp);
        mapHint=mapLiveText;

        Button mapPlus=smallButton("＋");mapPlus.setTextSize(22);
        FrameLayout.LayoutParams plusLp=new FrameLayout.LayoutParams(dp(48),dp(48),Gravity.END|Gravity.TOP);
        plusLp.setMargins(0,dp(12),dp(12),0);mapHolder.addView(mapPlus,plusLp);
        Button mapMinus=smallButton("−");mapMinus.setTextSize(22);
        FrameLayout.LayoutParams minusLp=new FrameLayout.LayoutParams(dp(48),dp(48),Gravity.END|Gravity.TOP);
        minusLp.setMargins(0,dp(62),dp(12),0);mapHolder.addView(mapMinus,minusLp);

        mapDetailPanel=new LinearLayout(this);mapDetailPanel.setOrientation(LinearLayout.VERTICAL);
        mapDetailPanel.setPadding(dp(16),dp(15),dp(16),dp(15));
        mapDetailPanel.setBackground(round(Color.argb(250,255,255,255),20,Color.rgb(214,228,238),1));
        mapDetailPanel.setVisibility(View.GONE);
        FrameLayout.LayoutParams detailLp=new FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM);
        detailLp.setMargins(dp(12),0,dp(12),dp(12));mapHolder.addView(mapDetailPanel,detailLp);

        c.addView(mapHolder,lp(-1,dp(580),0,0,0,0));

        zi.setOnClickListener(v->map.zoomBy(1.25f));zo.setOnClickListener(v->map.zoomBy(.8f));
        mapPlus.setOnClickListener(v->map.zoomBy(1.25f));mapMinus.setOnClickListener(v->map.zoomBy(.8f));
        reset.setOnClickListener(v->{map.resetView();if(mapDetailPanel!=null)mapDetailPanel.setVisibility(View.GONE);});
        d3.setOnClickListener(v->{map.toggleTerrain();d3.setText(map.terrain?"▱ "+t("2D नक्सा","2D map"):"◇ "+t("3D भू-आकृति","3D terrain"));});
        close.setOnClickListener(v->{
            boolean showing=mapHolder.getVisibility()==View.VISIBLE;
            mapHolder.setVisibility(showing?View.GONE:View.VISIBLE);
            close.setText(showing?"🗺️ "+t("नदी नक्सा खोल्नुहोस्","Open river map"):"✕ "+t("नदी नक्सा बन्द गर्नुहोस्","Close river map"));
        });
        return c;
    }

    private void updateMapLiveOverlay(){
        if(mapLiveText==null)return;
        int total=0,latest=0,normal=0,alert=0,warning=0,danger=0,missing=0;
        synchronized(stations){
            total=stations.size();
            for(RiverStation s:stations){
                if(s==null)continue;
                if(s.fresh)latest++;else missing++;
                if("danger".equals(s.stage))danger++;
                else if("warning".equals(s.stage))warning++;
                else if("alert".equals(s.stage))alert++;
                else if("normal".equals(s.stage))normal++;
            }
        }
        String line1=t("🌊 BIPAD नदी Official Live Feed","🌊 BIPAD River Official Live Feed");
        String line2=t(total+" official स्टेशन • "+latest+" latest reading • "+missing+" latest छैन • 🟢 official feed connected",
                       total+" official stations • "+latest+" latest readings • "+missing+" not latest • 🟢 official feed connected");
        String line3=t("🔵 सामान्य "+normal+"   🟡 सतर्क "+alert+"   🟠 चेतावनी "+warning+"   🔴 खतरा "+danger+"   ⚪ डाटा छैन "+missing,
                       "🔵 Normal "+normal+"   🟡 Alert "+alert+"   🟠 Warning "+warning+"   🔴 Danger "+danger+"   ⚪ No data "+missing);
        mapLiveText.setText(line1+"\n"+line2+"\n"+line3);
    }

    private void showMapDetail(String title,String detail){
        if(mapDetailPanel==null)return;
        mapDetailPanel.removeAllViews();
        LinearLayout top=new LinearLayout(this);top.setOrientation(LinearLayout.HORIZONTAL);top.setGravity(Gravity.CENTER_VERTICAL);
        TextView h=text(title==null?"":title,21,true,Color.rgb(16,39,70));top.addView(h,new LinearLayout.LayoutParams(0,-2,1f));
        TextView x=text("✕",20,true,Color.rgb(77,105,124));x.setGravity(Gravity.CENTER);x.setPadding(dp(10),dp(5),dp(10),dp(5));
        x.setOnClickListener(v->mapDetailPanel.setVisibility(View.GONE));top.addView(x);
        mapDetailPanel.addView(top);

        TextView section=text(t("◷ पछिल्लो official नदी reading","◷ Latest official river reading"),14,true,Color.rgb(30,52,72));
        section.setPadding(0,dp(9),0,dp(7));mapDetailPanel.addView(section);

        TextView body=text(detail==null?"":detail,13,false,Color.rgb(49,72,89));
        body.setPadding(dp(13),dp(11),dp(13),dp(11));
        body.setBackground(round(Color.rgb(255,249,226),15,Color.rgb(242,193,75),1));
        mapDetailPanel.addView(body);

        TextView source=text(t("BIPAD / DHM official source • stale data लाई live खतरा मानिँदैन।",
                               "BIPAD / DHM official source • stale data is never treated as a live threat."),
                             11,false,Color.rgb(95,122,141));
        source.setPadding(dp(2),dp(9),dp(2),0);mapDetailPanel.addView(source);
        mapDetailPanel.setVisibility(View.VISIBLE);
    }

'''
a=a[:start]+map_card+a[end:]

# Station taps now use the in-map white detail card, never a dimmed modal.
ss=a.find('    private void showStation(RiverStation s){')
se=a.find('    private void refreshHuman()',ss)
if ss<0 or se<0:
    raise SystemExit('showStation anchors missing')
station=r'''    private void showStation(RiverStation s){
        if(s==null)return;
        StringBuilder b=new StringBuilder();
        if(s.district!=null&&!s.district.trim().isEmpty())b.append(t("जिल्ला: ","District: ")).append(s.district.trim()).append("\n");
        b.append(stageDot(s.stage)).append(" ").append(stageName(s.stage));
        b.append("\n").append(t("पानीको सतह: ","Water level: ")).append(Double.isFinite(s.level)?String.format(Locale.US,"%.3f m",s.level):"—");
        if(Double.isFinite(s.warning))b.append("\nWarning: ").append(String.format(Locale.US,"%.3f m",s.warning));
        if(Double.isFinite(s.danger))b.append("\nDanger: ").append(String.format(Locale.US,"%.3f m",s.danger));
        if(s.at>0)b.append("\n").append(t("Official time: ","Official time: ")).append(Instant.ofEpochMilli(s.at).atZone(ZoneId.of("Asia/Kathmandu")).toLocalDateTime());
        b.append("\n").append(t("स्थिति: ","Status: ")).append(stageName(s.stage));
        showMapDetail(s.name,b.toString());
    }

'''
a=a[:ss]+station+a[se:]

# Match the four-item bottom navigation used by the target app mock/video.
bn=a.find('    private View bottomNav(){')
be=a.find('    private FrameLayout.LayoutParams bottomParams()',bn)
if bn<0 or be<0:
    raise SystemExit('bottomNav anchors missing')
bottom=r'''    private View bottomNav(){
        LinearLayout nav=new LinearLayout(this);nav.setOrientation(LinearLayout.HORIZONTAL);nav.setPadding(dp(7),dp(6),dp(7),dp(6));
        nav.setBackground(round(Color.argb(248,255,255,255),24,Color.rgb(208,227,237),1));
        Button h=navButton("⌂\n"+t("गृह","Home"));
        Button m=navButton("🗺️\n"+t("नदी नक्सा","River map"));
        Button n=navButton("🔔\n"+t("सूचना","Alerts"));
        Button more=navButton("☰\n"+t("थप","More"));
        nav.addView(h,weight());nav.addView(m,weight());nav.addView(n,weight());nav.addView(more,weight());
        h.setOnClickListener(v->smoothTo(homeAnchor));
        m.setOnClickListener(v->{smoothTo(mapAnchor);if(mapHolder!=null)mapHolder.setVisibility(View.VISIBLE);});
        n.setOnClickListener(v->smoothTo(newsAnchor));
        more.setOnClickListener(v->scroll.post(()->scroll.fullScroll(View.FOCUS_DOWN)));
        return nav;
    }
'''
a=a[:bn]+bottom+a[be:]

# Target wording from the video.
a,n1=re.subn(r'mapTitle\.setText\(t\("[^"]*","[^"]*"\)\);',
             'mapTitle.setText(t("🇳🇵 प्रत्यक्ष नदी प्रवाह नक्सा","🇳🇵 Live river flow map"));',a,count=1)
if n1!=1: raise SystemExit('mapTitle assignment missing')
a,n2=re.subn(r'mapSub\.setText\(t\("[^"]*","[^"]*"\)\);',
             'mapSub.setText(t("जिल्ला नाम + नेपालभित्र actual नदी • पातलो cyan=geometry • Glow/रङ=current official gauge • नदी tap गर्दा विवरण","District names + Nepal-only actual rivers • thin cyan=geometry • glow/colour=current official gauge • tap a river for details"));',a,count=1)
if n2!=1: raise SystemExit('mapSub assignment missing')

# Keep the black overlay live after feed refresh and on first render.
if 'map.setStations(copy,lat,lon);updateMapLiveOverlay();' not in a:
    if 'map.setStations(copy,lat,lon);' not in a: raise SystemExit('map setStations anchor missing')
    a=a.replace('map.setStations(copy,lat,lon);','map.setStations(copy,lat,lon);updateMapLiveOverlay();',1)
if 'applyLanguage();updateMapLiveOverlay();return root;' not in a:
    if 'applyLanguage();return root;' not in a: raise SystemExit('buildScreen applyLanguage anchor missing')
    a=a.replace('applyLanguage();return root;','applyLanguage();updateMapLiveOverlay();return root;',1)

# Version bump from v0.8.25.
g=g.replace('versionCode 45','versionCode 46',1).replace("versionName '0.8.25'","versionName '0.8.26'",1)
if 'versionCode 46' not in g or "versionName '0.8.26'" not in g:
    raise SystemExit('v0.8.26 version bump failed')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')

# Hard build gates: no regression to the v0.8.25 truth model, and no map modal.
a2=a_path.read_text(encoding='utf-8');m2=m_path.read_text(encoding='utf-8')
for marker in ['mapDetailPanel','BIPAD नदी Official Live Feed','updateMapLiveOverlay','नदी नक्सा बन्द गर्नुहोस्','private void showMapDetail','private void showStation']:
    if marker not in a2: raise SystemExit('video UI marker missing: '+marker)
for marker in ['currentFlowRivers','viewportInsideNepalStrict','clipWaysToNepalDense','routeD<=0.75','RiverTapInfo']:
    if marker not in m2: raise SystemExit('v0.8.25 truth marker missing: '+marker)
if 'new AlertDialog.Builder(this).setTitle(s.name)' in a2:
    raise SystemExit('station modal still present')
if 'stationTapListener.onStationTap(new RiverTapInfo' not in m2:
    raise SystemExit('river tap was not routed to in-map panel')
print('FloodSafe v0.8.26 video-match native river map UI PASS')
