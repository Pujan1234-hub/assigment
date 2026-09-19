from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
w_path=src/'RiverAlertWorker.java'
f_path=src/'FloodSafeMessagingService.java'
g_path=root/'app/build.gradle'

a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
w=w_path.read_text(encoding='utf-8')
f=f_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.67: latest-official-source parity.
# A station is CURRENT when it is present in the latest official BIPAD/DHM source and
# has a real observation. FloodSafe no longer invents a 5/20/30/40-minute cutoff.
# The official measurement timestamp/age is still shown exactly for transparency.
# Catalog/history-only stations remain unavailable/black because _floodsafeOnline=false.
# 2 km warning/danger radius, official thresholds, station coordinates and source polling stay intact.

def method_span(text,name):
    q=re.search(r'(?m)^\s*private\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',text)
    if not q:return None
    op=text.find('{',q.start());depth=0;quote=None;esc=False;i=op
    while i<len(text):
        ch=text[i]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in ('\"',"'"):quote=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return q.start(),i+1
        i+=1
    return None

# -----------------------------------------------------------------------------
# 1) Native station truth: latest-source membership, not local elapsed minutes.
# -----------------------------------------------------------------------------
old_fresh='boolean fresh=online&&hasObservation&&now-at<=20L*60L*1000L&&at-now<=5L*60L*1000L; // V0858_FRESH20_DISPLAY_OLD'
new_fresh='boolean fresh=online&&hasObservation; // V0867_SOURCE_CURRENT_NOT_AGE_GATED'
if old_fresh in a:
    a=a.replace(old_fresh,new_fresh,1)
elif 'V0867_SOURCE_CURRENT_NOT_AGE_GATED' not in a:
    raise SystemExit('v0867 parseStation freshness anchor missing')

# Any remaining compatibility use of this constant must not re-introduce a minute gate.
if 'RIVER_FRESH_MS=20L*60L*1000L' in a:
    a=a.replace('RIVER_FRESH_MS=20L*60L*1000L','RIVER_FRESH_MS=Long.MAX_VALUE',1)
elif 'RIVER_FRESH_MS=Long.MAX_VALUE' not in a:
    raise SystemExit('v0867 native freshness constant anchor missing')

refresh=r'''    private void refreshRiverUi(){
        if(nearList==null)return;List<RiverStation> copy;synchronized(stations){copy=new ArrayList<>(stations);}
        copy.sort(Comparator.comparingInt((RiverStation s)->s.online?0:1).thenComparingInt(s->s.rank).thenComparing(s->s.name,String.CASE_INSENSITIVE_ORDER));
        map.setStations(copy,lat,lon);

        int online=0,current=0,d=0,w=0,al=0,n=0;
        for(RiverStation s:copy){
            if(s.online)online++;
            if(s.fresh){current++;if("danger".equals(s.stage))d++;else if("warning".equals(s.stage))w++;else if("alert".equals(s.stage))al++;else if("normal".equals(s.stage))n++;}
        }
        int sourceTotal=Math.max(v849CatalogCount,copy.size());
        stationCount.setText(String.valueOf(sourceTotal));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));
        feedFresh.setText(t("आधिकारिक स्रोत अहिले: मापन "+current+" / "+sourceTotal+" • 🟢 स्रोतमा "+online+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n,
                "Official source now: readings "+current+" / "+sourceTotal+" • 🟢 in source "+online+" • 🔴 "+d+" 🟠 "+w+" 🟡 "+al+" 🔵 "+n)); // V0867_SOURCE_PARITY_SUMMARY
        updateRisk(copy);

        nearList.removeAllViews();
        if(!Double.isFinite(lat)||!Double.isFinite(lon)){
            nearSub.setText(t("हालको जीपीएस लिएपछि वास्तविक नजिकका मापन केन्द्र देखिन्छन्।","Get current GPS to show the actual nearest river stations."));
            nearList.addView(empty(t("◎ मेरो हालको स्थान थिचेर जीपीएस स्थान लिनुहोस्।","Tap My current location to get your GPS position.")));
        }else if(!isNepal(lat,lon)){
            nearSub.setText(t("तपाईं अहिले नेपाल बाहिर हुनुहुन्छ।","You are currently outside Nepal."));
            nearList.addView(empty(t("नेपाल बाहिर हुँदा नजिकका नेपाल नदी मापन केन्द्र देखाइँदैन।","Nearby Nepal river stations are not shown while you are outside Nepal.")));
        }else{
            nearSub.setText(t("तपाईंको हालको जीपीएसबाट दूरीअनुसार नजिकका आधिकारिक नदी मापन केन्द्र","Official river stations nearest to your current GPS, sorted by distance"));
            List<RiverStation> near=new ArrayList<>(copy);near.sort(Comparator.comparingDouble(s->distanceKm(s.lat,s.lon)));
            for(int i=0;i<Math.min(8,near.size());i++)nearList.addView(stationRow(near.get(i)));
            if(near.isEmpty())nearList.addView(empty(t("नजिकको आधिकारिक नदी मापन केन्द्र भेटिएन।","No nearby official river station was found.")));
        }

        if(nationalList!=null){
            nationalList.removeAllViews();
            if(selectedDistrict.isEmpty()){
                nationalFresh.setText(t("जिल्ला छानेर आधिकारिक स्रोतमा अहिले उपलब्ध पानी-सतह मापन हेर्नुहोस्।","Choose a district to view water-level readings currently present in the official source."));
                nationalList.addView(empty(t("माथिबाट जिल्ला छान्नुहोस्।","Choose a district above.")));
            }else{
                int currentWater=0;
                for(RiverStation s:copy){
                    if(selectedDistrict.equalsIgnoreCase(s.district)&&s.fresh&&v0857WaterLevelStation(s)){
                        currentWater++;nationalList.addView(stationRow(s));
                    }
                }
                nationalFresh.setText(t(selectedDistrict+": आधिकारिक स्रोतमा अहिले उपलब्ध पानी-सतह केन्द्र "+currentWater,
                        selectedDistrict+": water-level stations currently in official source "+currentWater));
                if(currentWater==0)nationalList.addView(empty(t("आधिकारिक स्रोतमा अहिले पानी-सतह मापन उपलब्ध छैन। Rainfall र velocity छुट्टै data हुन्।","No water-level reading is currently available in the official source. Rainfall and velocity are separate data types.")));
            }
        }
    } // V0867_NO_MINUTE_CUTOFF_UI
'''
sp=method_span(a,'refreshRiverUi')
if not sp:raise SystemExit('v0867 refreshRiverUi missing')
a=a[:sp[0]]+refresh+a[sp[1]:]

station_line=r'''    private String stationLine(RiverStation s){
        boolean has=Double.isFinite(s.level)&&s.at>0L;
        String lev=Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):t("सतह उपलब्ध छैन","level unavailable");
        String state;if(!s.online)state=t("हालको आधिकारिक स्रोतमा छैन","not in current official source");else if(!has)state=t("मापन उपलब्ध छैन","measurement unavailable");else state=stageName(s.stage);
        double km=distanceKm(s.lat,s.lon);String dist=Double.isFinite(km)?String.format(Locale.US," • %.1f km",km):"";
        return state+" • "+lev+" • "+v850Age(s.at)+dist;
    } // V0867_STATION_SOURCE_TIME
'''
sp=method_span(a,'stationLine')
if not sp:raise SystemExit('v0867 stationLine missing')
a=a[:sp[0]]+station_line+a[sp[1]:]

station_detail=r'''    private void showStation(RiverStation s){
        if(s==null)return;
        boolean hasReading=Double.isFinite(s.level)&&s.at>0;
        StringBuilder b=new StringBuilder();
        b.append(v849AvailabilityDot(s)).append(" ").append(s.online?t("पछिल्लो आधिकारिक स्रोतमा उपलब्ध","Available in latest official source"):t("पछिल्लो आधिकारिक स्रोतमा उपलब्ध छैन","Not in latest official source"));
        if(hasReading){
            b.append("\n").append(t("अवस्था: ","Status: ")).append(stageName(s.stage));
            b.append("\n\n").append(t("आधिकारिक पानीको सतह: ","Official water level: ")).append(String.format(Locale.US,"%.2f m",s.level));
            b.append("\n").append(t("स्रोतको मापन समय: ","Official measurement time: ")).append(v848Time(s.at));
            b.append("\n").append(t("स्रोत समयदेखि: ","Source age: ")).append(v850Age(s.at));
            if(Double.isFinite(s.warning))b.append("\n").append(t("चेतावनी तह: ","Warning level: ")).append(String.format(Locale.US,"%.2f m",s.warning));
            if(Double.isFinite(s.danger))b.append("\n").append(t("खतरा तह: ","Danger level: ")).append(String.format(Locale.US,"%.2f m",s.danger));
            if(s.online)b.append("\n\n").append(t("यो आधिकारिक स्रोतमा अहिले देखिएको पछिल्लो मापन हो। एपले ५/२०/३०/४० मिनेटको आफ्नै सीमा लगाउँदैन।","This is the latest reading currently shown by the official source. The app applies no local 5/20/30/40-minute cutoff."));
            else b.append("\n\n").append(t("यो इतिहासमा रहेको अन्तिम आधिकारिक मापन हो; हालको आधिकारिक स्रोतमा यो स्टेशन उपलब्ध छैन।","This is the last historical official reading; the station is not present in the current official source."));
        }else{
            b.append("\n\n").append(t("यो मापन केन्द्रका लागि आधिकारिक पानी-सतह र मापन समय अहिले उपलब्ध छैन।","Official water level and measurement time are not currently available for this station."));
        }
        b.append("\n\n").append(t("स्रोत: BIPAD/DHM आधिकारिक नदी मापन","Source: official BIPAD/DHM river measurement"));
        new AlertDialog.Builder(this).setTitle(s.name).setMessage(b.toString()).setPositiveButton(t("ठीक छ","OK"),null).show();
    } // V0867_STATION_DETAIL_SOURCE_PARITY
'''
sp=method_span(a,'showStation')
if not sp:raise SystemExit('v0867 showStation missing')
a=a[:sp[0]]+station_detail+a[sp[1]:]

# Remove surviving visible age-window wording from older layers.
for old,new in [
    ('पछिल्लो २० मिनेटभित्रको आधिकारिक मापन मात्र','आधिकारिक स्रोतमा अहिले उपलब्ध पछिल्लो मापन'),
    ('पछिल्लो २० मिनेट','पछिल्लो आधिकारिक स्रोत'),
    ('२० मिनेटभन्दा पुरानो मापन','हालको आधिकारिक स्रोतमा नभएको मापन'),
    ('Only a matching official reading from the last 20 minutes is shown here.','Only a matching reading currently present in the official source is shown here.'),
    ('Live river status uses only an official reading from the last 20 minutes.','Live river status mirrors the latest official source.'),
    ('within the last 20 minutes','in the latest official source'),
    ('last 20 minutes','latest official source'),
    ('20-minute safety freshness','latest-official-source status')]:
    a=a.replace(old,new)

# -----------------------------------------------------------------------------
# 2) Map river detail: same source-current semantics, still geometry-safe.
# -----------------------------------------------------------------------------
show_river=r'''    private void showRiver(RiverWay r,double la,double lo) {
        StationDot gauge=v866RiverGauge(r,la,lo);
        boolean named=v863UsefulRiverName(r==null?null:r.name);
        String riverName=named?r.name:(englishUi?"Unnamed river / stream":"नाम नखुलेको नदी / खोला");
        StringBuilder msg=new StringBuilder();
        if(gauge!=null){
            double tapD=km(la,lo,gauge.lat,gauge.lon);
            double routeD=v866PointToRiverKm(r,gauge.lat,gauge.lon);
            msg.append("🟢 ").append(englishUi?"Official station for this river: ":"यस नदीसँग जोडिएको आधिकारिक मापन केन्द्र: ").append(gauge.name);
            if(Double.isFinite(tapD))msg.append(String.format(Locale.US," • %.1f km",tapD));
            if(Double.isFinite(gauge.level))msg.append(String.format(Locale.US,englishUi?"\nOfficial water level: %.2f m":"\nआधिकारिक पानीको सतह: %.2f m",gauge.level));
            if(gauge.at>0L){
                msg.append("\n").append(englishUi?"Official measurement time: ":"आधिकारिक मापन समय: ").append(v0861MapTime(gauge.at));
                msg.append("\n").append(englishUi?"Source age: ":"स्रोत समयदेखि: ").append(v0861MapAge(gauge.at));
            }
            if(Double.isFinite(gauge.warning))msg.append(String.format(Locale.US,englishUi?"\nWarning level: %.2f m":"\nचेतावनी तह: %.2f m",gauge.warning));
            if(Double.isFinite(gauge.danger))msg.append(String.format(Locale.US,englishUi?"\nDanger level: %.2f m":"\nखतरा तह: %.2f m",gauge.danger));
            msg.append("\n").append(englishUi?"Status: ":"अवस्था: ").append(v0861MapStage(gauge.stage));
            if(Double.isFinite(routeD))msg.append(String.format(Locale.US,englishUi?"\nGauge-to-map-river distance: %.1f km":"\nमापन केन्द्र–नक्सा नदी दूरी: %.1f km",routeD));
            msg.append("\n\n").append(englishUi?"FloodSafe mirrors the latest official source and does not impose a local minute cutoff.":"FloodSafe ले पछिल्लो आधिकारिक स्रोत जस्ताको तस्तै देखाउँछ; एपले आफ्नै मिनेट सीमा लगाउँदैन।");
        }else{
            msg.append(englishUi?"No water-level station currently present in the official source can be safely associated with this exact river segment.":"हालको आधिकारिक स्रोतमा यो नदीको यही खण्डसँग सुरक्षित रूपमा जोड्न मिल्ने पानी-सतह मापन केन्द्र भेटिएन।");
            msg.append("\n\n").append(englishUi?"Tap a station dot directly to see that exact station. FloodSafe will not borrow a distant or different-river gauge.":"ठ्याक्कै मापन केन्द्रको जानकारी हेर्न स्टेशन डट नै थिच्नुहोस्। FloodSafe ले टाढाको वा अर्को नदीको मापन यहाँ जोड्दैन।");
        }
        msg.append("\n\n").append(englishUi?"River geometry: OpenStreetMap / FloodSafe Nepal network":"नदी नक्सा: OpenStreetMap / FloodSafe Nepal नदी सञ्जाल");
        new AlertDialog.Builder(getContext()).setTitle(riverName).setMessage(msg.toString()).setPositiveButton(englishUi?"OK":"ठीक छ",null).show();
    } // V0867_RIVER_SOURCE_PARITY
'''
sp=method_span(m,'showRiver')
if not sp:raise SystemExit('v0867 showRiver missing')
m=m[:sp[0]]+show_river+m[sp[1]:]

m=m.replace('if(s==null||!s.fresh||!Double.isFinite(s.level)||s.at<=0L)continue;',
            'if(s==null||!s.fresh||!Double.isFinite(s.level)||s.at<=0L)continue; // V0867_FRESH_MEANS_LATEST_SOURCE',1)
for old,new in [
    ('last 20 minutes','latest official source'),
    ('20-minute safety freshness','latest-official-source status'),
    ('पछिल्लो २० मिनेटभित्रको','पछिल्लो आधिकारिक स्रोतमा उपलब्ध')]:
    m=m.replace(old,new)

# -----------------------------------------------------------------------------
# 3) Closed-app local alert acceptance: trust the current official feed row; do not
#    discard it because its official timestamp is 21/30/40+ minutes old.
# -----------------------------------------------------------------------------
worker_gate='''        if (measuredAt <= 0L || now - measuredAt > MAX_AGE_MS || measuredAt - now > FUTURE_TOLERANCE_MS) {\n            return null;\n        }'''
if worker_gate in w:
    w=w.replace(worker_gate,'        if (measuredAt <= 0L) return null; // V0867_WORKER_SOURCE_TIME_NO_LOCAL_AGE_GATE',1)
elif 'V0867_WORKER_SOURCE_TIME_NO_LOCAL_AGE_GATE' not in w:
    raise SystemExit('v0867 worker age gate anchor missing')
w=w.replace('    private static final long MAX_AGE_MS = 20L * 60L * 1000L;\n','')
w=w.replace('    private static final long FUTURE_TOLERANCE_MS = 5L * 60L * 1000L;\n','')

fcm_gate='if(measuredAt<=0L||now-measuredAt>MAX_RIVER_AGE_MS||measuredAt-now>FUTURE_TOLERANCE_MS)return false;'
if fcm_gate in f:
    f=f.replace(fcm_gate,'if(measuredAt<=0L)return false; // V0867_FCM_SOURCE_TIME_NO_LOCAL_AGE_GATE',1)
elif 'V0867_FCM_SOURCE_TIME_NO_LOCAL_AGE_GATE' not in f:
    raise SystemExit('v0867 FCM age gate anchor missing')
f=f.replace('    private static final long MAX_RIVER_AGE_MS = 20L * 60L * 1000L;\n','')
f=f.replace('    private static final long FUTURE_TOLERANCE_MS = 5L * 60L * 1000L;\n','')

# -----------------------------------------------------------------------------
# 4) Build identity.
# -----------------------------------------------------------------------------
if 'versionCode 86' in g:g=g.replace('versionCode 86','versionCode 87',1)
elif 'versionCode 87' not in g:raise SystemExit('v0867 versionCode anchor missing')
if "versionName '0.8.66'" in g:g=g.replace("versionName '0.8.66'","versionName '0.8.67'",1)
elif "versionName '0.8.67'" not in g:raise SystemExit('v0867 versionName anchor missing')

for p,t in [(a_path,a),(m_path,m),(w_path,w),(f_path,f),(g_path,g)]:p.write_text(t,encoding='utf-8')

# Hard guards.
for x in ['V0867_SOURCE_CURRENT_NOT_AGE_GATED','V0867_SOURCE_PARITY_SUMMARY','V0867_NO_MINUTE_CUTOFF_UI','V0867_STATION_SOURCE_TIME','V0867_STATION_DETAIL_SOURCE_PARITY','RIVER_FRESH_MS=Long.MAX_VALUE','main.postDelayed(this,10_000L);']:
    if x not in a:raise SystemExit('v0867 activity verification failed: '+x)
for x in ['V0867_RIVER_SOURCE_PARITY','V0867_FRESH_MEANS_LATEST_SOURCE','V0866_STATION_TAP_FIRST','V0866_POINT_SEGMENT_DISTANCE']:
    if x not in m:raise SystemExit('v0867 map verification failed: '+x)
for x in ['V0867_WORKER_SOURCE_TIME_NO_LOCAL_AGE_GATE','RADIUS_KM = 2d']:
    if x not in w:raise SystemExit('v0867 worker verification failed: '+x)
for x in ['V0867_FCM_SOURCE_TIME_NO_LOCAL_AGE_GATE','DEFAULT_RIVER_RADIUS_KM = 2d']:
    if x not in f:raise SystemExit('v0867 FCM verification failed: '+x)
if 'now-at<=20L*60L*1000L' in a:raise SystemExit('v0867 native 20-minute gate still active')
if 'MAX_AGE_MS = 20L * 60L * 1000L' in w:raise SystemExit('v0867 worker 20-minute gate still active')
if 'MAX_RIVER_AGE_MS = 20L * 60L * 1000L' in f:raise SystemExit('v0867 FCM 20-minute gate still active')
for x in ['versionCode 87',"versionName '0.8.67'"]:
    if x not in g:raise SystemExit('v0867 version verification failed: '+x)

print('FloodSafe v0.8.67 PASS: latest official BIPAD/DHM source parity, no local minute cutoff; official timestamp retained; 2 km alert radius unchanged')
