from pathlib import Path
import re

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.63: a river tap must never borrow an unrelated nearest gauge.
# - exact station dots still open that station
# - river lines only show a fresh <=20 min gauge whose river name matches the tapped river
# - unnamed river geometry never displays an arbitrary nearby station
# - progressive tier names are preserved by the v0.8.63 asset builder change
# Safety radius, alert thresholds, source polling, GPS, colours and animation stay unchanged.

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

# Make sure the post-v0.8.61 StationDot shape contains the fields used below.
for field in ['online','fresh','name','level','warning','danger','at','stage']:
    if field not in m: raise SystemExit('v0863 required station field missing: '+field)

show=r'''    private void showRiver(RiverWay r,double la,double lo) {
        StationDot gauge=v863SameRiverGauge(r,la,lo);
        boolean named=v863UsefulRiverName(r==null?null:r.name);
        String riverName=named?r.name:(englishUi?"Unnamed river / stream":"नाम नखुलेको नदी / खोला");
        StringBuilder msg=new StringBuilder();
        if(gauge!=null){
            double d=km(la,lo,gauge.lat,gauge.lon);
            msg.append("🟢 ").append(englishUi?"Matching official station: ":"यसै नदीको आधिकारिक मापन केन्द्र: ")
                    .append(gauge.name).append(String.format(Locale.US," • %.1f km",d));
            if(Double.isFinite(gauge.level))msg.append(String.format(Locale.US,englishUi?"\nLatest official water level: %.2f m":"\nपछिल्लो आधिकारिक पानीको सतह: %.2f m",gauge.level));
            if(gauge.at>0L){
                msg.append("\n").append(englishUi?"Measurement time: ":"मापन समय: ").append(v0861MapTime(gauge.at));
                msg.append("\n").append(englishUi?"Age: ":"कति अघि: ").append(v0861MapAge(gauge.at));
            }
            if(Double.isFinite(gauge.warning))msg.append(String.format(Locale.US,englishUi?"\nWarning level: %.2f m":"\nचेतावनी तह: %.2f m",gauge.warning));
            if(Double.isFinite(gauge.danger))msg.append(String.format(Locale.US,englishUi?"\nDanger level: %.2f m":"\nखतरा तह: %.2f m",gauge.danger));
            msg.append("\n").append(englishUi?"Safety status: ":"सुरक्षा अवस्था: ").append(v0861MapStage(gauge.stage));
            msg.append("\n\n").append(englishUi?"Only a matching official reading from the last 20 minutes is shown here.":"यहाँ यही नदीसँग मिलेको पछिल्लो २० मिनेटभित्रको आधिकारिक मापन मात्र देखाइन्छ।");
        }else{
            if(named){
                msg.append(englishUi?"No matching official water-level reading for this river is available within the last 20 minutes.":"यस नदीसँग मिल्ने पछिल्लो २० मिनेटभित्रको आधिकारिक पानी-सतह मापन अहिले उपलब्ध छैन।");
            }else{
                msg.append(englishUi?"This map segment has no usable river name in the source data, so FloodSafe will not attach an unrelated nearby gauge.":"यो नक्सा खण्डको स्रोतमा प्रयोग गर्न मिल्ने नदीको नाम छैन, त्यसैले असम्बन्धित नजिकको मापन केन्द्र यहाँ जोडिँदैन।");
            }
            msg.append("\n\n").append(englishUi?"No old or different-river station is shown as live.":"पुरानो वा अर्को नदीको मापनलाई प्रत्यक्ष भनेर देखाइँदैन।");
        }
        msg.append("\n\n").append(englishUi?"River geometry: OpenStreetMap / FloodSafe Nepal network":"नदी नक्सा: OpenStreetMap / FloodSafe Nepal नदी सञ्जाल");
        new AlertDialog.Builder(getContext()).setTitle(riverName).setMessage(msg.toString()).setPositiveButton(englishUi?"OK":"ठीक छ",null).show();
    } // V0863_RIVER_TAP_TRUTH

    private StationDot v863SameRiverGauge(RiverWay r,double la,double lo){
        if(r==null||!v863UsefulRiverName(r.name))return null;
        String rk=v863RiverCore(r.name);if(rk.isEmpty())return null;
        StationDot best=null;double bestD=Double.POSITIVE_INFINITY;
        synchronized(stations){for(StationDot s:stations){
            if(s==null||!s.fresh||s.name==null)continue; // current safety window only
            String sk=v863RiverCore(s.name);if(sk.isEmpty()||!v863RiverNamesMatch(rk,sk))continue;
            double d=km(la,lo,s.lat,s.lon);if(d<bestD){bestD=d;best=s;}
        }}
        return bestD<=120.0?best:null;
    } // V0863_SAME_RIVER_GAUGE

    private static boolean v863UsefulRiverName(String s){
        if(s==null)return false;String x=s.trim().toLowerCase(Locale.ROOT);
        return !x.isEmpty()&&!x.equals("river")&&!x.equals("stream")&&!x.equals("river / stream")&&!x.equals("नदी / खोला")&&!x.equals("नदी/खोला");
    }
    private static String v863RiverCore(String s){
        if(s==null)return "";String x=s.toLowerCase(Locale.ROOT);
        x=x.replaceAll("\\([^)]*\\)"," ");
        x=x.replaceAll("\\s+(at|near)\\s+.*$"," ");
        x=x.replaceAll("(?iu)\\b(river|khola|khola|nadi|gauge|station|rls|hydrology|water level)\\b"," ");
        x=x.replace("नदी", " ").replace("खोला", " ").replace("खोला", " ");
        return x.replaceAll("[^\\p{L}\\p{Nd}]+","").trim();
    }
    private static boolean v863RiverNamesMatch(String a,String b){
        if(a.equals(b))return true;
        if(a.length()>=4&&b.contains(a))return true;
        if(b.length()>=4&&a.contains(b))return true;
        return false;
    }

'''
span=method_span(m,'showRiver')
if not span:raise SystemExit('v0863 showRiver method missing')
m=m[:span[0]]+show+m[span[1]:]

# Bump build identity only after v0.8.62 has finished.
if 'versionCode 82' in g:g=g.replace('versionCode 82','versionCode 83',1)
elif 'versionCode 83' not in g:raise SystemExit('v0863 versionCode anchor missing')
if "versionName '0.8.62'" in g:g=g.replace("versionName '0.8.62'","versionName '0.8.63'",1)
elif "versionName '0.8.63'" not in g:raise SystemExit('v0863 versionName anchor missing')

m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
for x in ['V0863_RIVER_TAP_TRUTH','V0863_SAME_RIVER_GAUGE','!s.fresh','v863RiverNamesMatch','V0861_RIVER_DETAIL_PARITY','V0852_MAPLIBRE_USER_LOCATION']:
    if x not in m:raise SystemExit('v0863 map verification failed: '+x)
for x in ['versionCode 83',"versionName '0.8.63'"]:
    if x not in g:raise SystemExit('v0863 version verification failed: '+x)
print('FloodSafe v0.8.63 PASS: river taps use same-river fresh gauge only; unnamed/unmatched lines never borrow an unrelated station')
