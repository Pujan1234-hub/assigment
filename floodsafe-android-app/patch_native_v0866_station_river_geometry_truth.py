from pathlib import Path
import re

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.66 field fix from real-device screenshots:
# - exact station taps take priority over the river line underneath them
# - river taps use geometry + name truth, never an unrelated far-away gauge
# - unnamed/mismatched river names may still use a fresh gauge only when the official
#   station is physically beside the rendered river geometry
# - reveal exact local OSM waterways a little earlier so small khola/streams near official
#   stations are less likely to disappear at normal city/district zoom
# - keep official station coordinates untouched; never visually move/snap a gauge
# - 20-minute safety freshness, 2 km emergency radius, alerts, polling and GPS unchanged

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

# 1) Tap priority: an exact visible station dot must open that exact station first.
# Tight geographic hit radius prevents a river tap from accidentally opening a gauge
# several kilometres away at low zoom.
click=r'''    private boolean onMapClick(LatLng p) {
        double zoom=map==null?6.0:map.getCameraPosition().zoom;

        StationDot nearest=nearestStation(p.getLatitude(),p.getLongitude());
        double stationThreshold=Math.max(0.16,Math.min(2.0,1.6/Math.pow(2.0,Math.max(0.0,zoom-7.0))));
        double sd=nearest==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),nearest.lat,nearest.lon);
        if(nearest!=null&&sd<=stationThreshold){
            if(stationTapListener!=null)stationTapListener.onStationTap(nearest.original);
            return true;
        } // V0866_STATION_TAP_FIRST

        RiverWay rw=nearestRiver(p.getLatitude(),p.getLongitude(),Math.max(0.10,3.2/Math.pow(2.0,Math.max(0.0,zoom-6.0))));
        if(rw!=null){showRiver(rw,p.getLatitude(),p.getLongitude());return true;}

        RainDot rain=nearestRain(p.getLatitude(),p.getLongitude());
        double rainThreshold=Math.max(0.28,Math.min(2.5,2.0/Math.pow(2.0,Math.max(0.0,zoom-7.0))));
        double rd=rain==null?Double.MAX_VALUE:km(p.getLatitude(),p.getLongitude(),rain.lat,rain.lon);
        if(rain!=null&&zoom>=7.0&&rd<=rainThreshold){showRain(rain);return true;}
        return false;
    } // V0866_TIGHT_TAP_TARGETS
'''
span=method_span(m,'onMapClick')
if not span:raise SystemExit('v0866 onMapClick missing')
m=m[:span[0]]+click+m[span[1]:]

# 2) River association: physical river geometry is authoritative, with river-name match
# as a strong signal. A fresh gauge may be used without a usable name only when it sits
# essentially on this rendered river. This fixes green-dot -> "no measurement" when the
# user actually tapped the gauge, while still preventing wrong-river substitution.
show=r'''    private void showRiver(RiverWay r,double la,double lo) {
        StationDot gauge=v866RiverGauge(r,la,lo);
        boolean named=v863UsefulRiverName(r==null?null:r.name);
        String riverName=named?r.name:(englishUi?"Unnamed river / stream":"नाम नखुलेको नदी / खोला");
        StringBuilder msg=new StringBuilder();
        if(gauge!=null){
            double tapD=km(la,lo,gauge.lat,gauge.lon);
            double routeD=v866PointToRiverKm(r,gauge.lat,gauge.lon);
            msg.append("🟢 ").append(englishUi?"Official station for this river: ":"यस नदीसँग जोडिएको आधिकारिक मापन केन्द्र: ")
                    .append(gauge.name);
            if(Double.isFinite(tapD))msg.append(String.format(Locale.US," • %.1f km",tapD));
            if(Double.isFinite(gauge.level))msg.append(String.format(Locale.US,englishUi?"\nLatest official water level: %.2f m":"\nपछिल्लो आधिकारिक पानीको सतह: %.2f m",gauge.level));
            if(gauge.at>0L){
                msg.append("\n").append(englishUi?"Measurement time: ":"मापन समय: ").append(v0861MapTime(gauge.at));
                msg.append("\n").append(englishUi?"Age: ":"कति अघि: ").append(v0861MapAge(gauge.at));
            }
            if(Double.isFinite(gauge.warning))msg.append(String.format(Locale.US,englishUi?"\nWarning level: %.2f m":"\nचेतावनी तह: %.2f m",gauge.warning));
            if(Double.isFinite(gauge.danger))msg.append(String.format(Locale.US,englishUi?"\nDanger level: %.2f m":"\nखतरा तह: %.2f m",gauge.danger));
            msg.append("\n").append(englishUi?"Safety status: ":"सुरक्षा अवस्था: ").append(v0861MapStage(gauge.stage));
            if(Double.isFinite(routeD))msg.append(String.format(Locale.US,englishUi?"\nGauge-to-map-river distance: %.1f km":"\nमापन केन्द्र–नक्सा नदी दूरी: %.1f km",routeD));
            msg.append("\n\n").append(englishUi?"Live river status uses only an official reading from the last 20 minutes.":"प्रत्यक्ष नदी अवस्था लागि पछिल्लो २० मिनेटभित्रको आधिकारिक मापन मात्र प्रयोग हुन्छ।");
        }else{
            msg.append(englishUi?"No fresh official water-level station can be safely associated with this exact river segment right now.":"यो नदीको यही खण्डसँग सुरक्षित रूपमा जोड्न मिल्ने पछिल्लो २० मिनेटभित्रको आधिकारिक पानी-सतह मापन अहिले छैन।");
            msg.append("\n\n").append(englishUi?"Tap a station dot directly to see that exact station. FloodSafe will not borrow a distant or different-river gauge.":"ठ्याक्कै मापन केन्द्रको जानकारी हेर्न हरियो/कालो स्टेशन डट नै थिच्नुहोस्। FloodSafe ले टाढाको वा अर्को नदीको मापन यहाँ जोड्दैन।");
        }
        msg.append("\n\n").append(englishUi?"River geometry: OpenStreetMap / FloodSafe Nepal network":"नदी नक्सा: OpenStreetMap / FloodSafe Nepal नदी सञ्जाल");
        new AlertDialog.Builder(getContext()).setTitle(riverName).setMessage(msg.toString()).setPositiveButton(englishUi?"OK":"ठीक छ",null).show();
    } // V0866_RIVER_GEOMETRY_TRUTH

    private StationDot v866RiverGauge(RiverWay r,double la,double lo){
        if(r==null||r.points==null||r.points.size()<2)return null;
        String rk=v863UsefulRiverName(r.name)?v863RiverCore(r.name):"";
        StationDot best=null;double bestScore=Double.POSITIVE_INFINITY;
        synchronized(stations){for(StationDot s:stations){
            if(s==null||!s.fresh||!Double.isFinite(s.level)||s.at<=0L)continue;
            double routeD=v866PointToRiverKm(r,s.lat,s.lon);if(!Double.isFinite(routeD))continue;
            String sk=s.name==null?"":v863RiverCore(s.name);
            boolean nameMatch=!rk.isEmpty()&&!sk.isEmpty()&&v863RiverNamesMatch(rk,sk);
            // Named rivers tolerate small OSM/official-coordinate offsets; unnamed or
            // text-mismatched features require the gauge to be physically very close.
            double routeLimit=nameMatch?6.0:1.8;
            if(routeD>routeLimit)continue;
            double tapD=km(la,lo,s.lat,s.lon);if(!Double.isFinite(tapD)||tapD>45.0)continue;
            double score=routeD*8.0+tapD+(nameMatch?0.0:12.0);
            if(score<bestScore){bestScore=score;best=s;}
        }}
        return best;
    } // V0866_GEOMETRY_FIRST_GAUGE

    private static double v866PointToRiverKm(RiverWay r,double lat,double lon){
        if(r==null||r.points==null||r.points.size()<2)return Double.POSITIVE_INFINITY;
        double cos=Math.cos(Math.toRadians(lat));if(Math.abs(cos)<0.1)cos=0.1;
        double best=Double.POSITIVE_INFINITY;
        for(int i=1;i<r.points.size();i++){
            double[] a=r.points.get(i-1),b=r.points.get(i);if(a==null||b==null||a.length<2||b.length<2)continue;
            double ax=(a[0]-lon)*111.32*cos,ay=(a[1]-lat)*110.57;
            double bx=(b[0]-lon)*111.32*cos,by=(b[1]-lat)*110.57;
            double vx=bx-ax,vy=by-ay,den=vx*vx+vy*vy;
            double t=den<=1e-12?0.0:-(ax*vx+ay*vy)/den;if(t<0)t=0;else if(t>1)t=1;
            double px=ax+t*vx,py=ay+t*vy,d=Math.sqrt(px*px+py*py);if(d<best)best=d;
        }
        return best;
    } // V0866_POINT_SEGMENT_DISTANCE
'''
span=method_span(m,'showRiver')
if not span:raise SystemExit('v0866 showRiver missing')
m=m[:span[0]]+show+m[span[1]:]

# 3) Small khola/stream geometry should appear before the old 8.20 threshold. This does
# not move station coordinates; it only renders the already-bundled exact OSM local tiles.
if 'if(zoom>=8.20)' in m:
    m=m.replace('if(zoom>=8.20)','if(zoom>=7.60)',1)
elif 'if(zoom>=7.60)' not in m:
    raise SystemExit('v0866 progressive exact-waterway threshold missing')
if 'V0866_EARLIER_EXACT_LOCAL_RIVERS' not in m:
    m=m.replace('if(zoom>=7.60){','if(zoom>=7.60){ // V0866_EARLIER_EXACT_LOCAL_RIVERS',1)

# Version bump only.
if 'versionCode 85' in g:g=g.replace('versionCode 85','versionCode 86',1)
elif 'versionCode 86' not in g:raise SystemExit('v0866 versionCode anchor missing')
if "versionName '0.8.65'" in g:g=g.replace("versionName '0.8.65'","versionName '0.8.66'",1)
elif "versionName '0.8.66'" not in g:raise SystemExit('v0866 versionName anchor missing')

m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

for x in ['V0866_STATION_TAP_FIRST','V0866_TIGHT_TAP_TARGETS','V0866_RIVER_GEOMETRY_TRUTH','V0866_GEOMETRY_FIRST_GAUGE','V0866_POINT_SEGMENT_DISTANCE','V0866_EARLIER_EXACT_LOCAL_RIVERS','V0863_RIVER_TAP_TRUTH','V0861_RIVER_DETAIL_PARITY','V0852_MAPLIBRE_USER_LOCATION']:
    if x not in m:raise SystemExit('v0866 map verification failed: '+x)
for x in ['versionCode 86',"versionName '0.8.66'"]:
    if x not in g:raise SystemExit('v0866 version verification failed: '+x)
print('FloodSafe v0.8.66 PASS: station-tap first + tight hit radius + geometry-safe river gauge matching + earlier exact local streams; 20m/2km safety unchanged')
