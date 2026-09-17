from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
map_path=src/'FloodSafeNativeMapView.java'
gradle_path=root/'app/build.gradle'
helper=map_path.read_text(encoding='utf-8')
gradle=gradle_path.read_text(encoding='utf-8')

show_pat=r'''    private void showRiver\(RiverWay r, double la, double lo\) \{.*?\n    \}\n\n    private StationDot directGaugeFor'''
show_new=r'''    private void showRiver(RiverWay r, double la, double lo) {
        StationDot direct = directGaugeFor(r, la, lo);
        String title=(r==null||r.name==null||r.name.trim().isEmpty())?"नदी / खोला":r.name;
        StringBuilder msg = new StringBuilder();
        if (direct != null) {
            double d=km(la,lo,direct.lat,direct.lon);
            msg.append("आजको प्रत्यक्ष official reading\n");
            msg.append("Gauge: ").append(direct.name).append(String.format(Locale.US," • %.1f km",d));
            if(Double.isFinite(direct.level))msg.append(String.format(Locale.US,"\nपानीको सतह: %.2f m",direct.level));
            if(Double.isFinite(direct.warning))msg.append(String.format(Locale.US,"\nWarning सीमा: %.2f m",direct.warning));
            if(Double.isFinite(direct.danger))msg.append(String.format(Locale.US,"\nDanger सीमा: %.2f m",direct.danger));
            msg.append("\nStatus: ").append(direct.stage==null?"UNKNOWN":direct.stage.toUpperCase(Locale.ROOT));
            msg.append("\nOfficial time: ").append(formatOfficialTime(direct.at));
        } else {
            msg.append("यो नदी/खोलाको आजको direct official reading उपलब्ध छैन।\n");
            msg.append("अर्को नदी/खोलाको gauge reference यहाँ देखाइँदैन।");
        }
        msg.append("\n\nनदी geometry: OpenStreetMap / FloodSafe network");
        new AlertDialog.Builder(getContext()).setTitle(title).setMessage(msg.toString()).setPositiveButton("ठीक छ", null).show();
    }

    private StationDot directGaugeFor'''
helper,n=re.subn(show_pat,show_new,helper,count=1,flags=re.S)
if n!=1: raise SystemExit('showRiver block missing')

direct_pat=r'''    private StationDot directGaugeFor\(RiverWay r,double la,double lo\)\{.*?\n    \}\n'''
direct_new=r'''    private StationDot directGaugeFor(RiverWay r,double la,double lo){
        String key=riverNameKey(r==null?"":r.name);if(key.length()<3)return null;StationDot best=null;double d=Double.MAX_VALUE;
        synchronized(stations){for(StationDot s:stations){
            if(s==null||!s.fresh||s.stage==null||"unknown".equalsIgnoreCase(s.stage))continue;
            String sk=riverNameKey(s.name);if(sk.length()<3)continue;
            boolean same=sk.equals(key)||sk.startsWith(key)||key.startsWith(sk);
            if(!same)continue;
            double x=km(la,lo,s.lat,s.lon);if(x<d&&x<=35.0){d=x;best=s;}
        }}return best;
    }
'''
helper,n=re.subn(direct_pat,direct_new,helper,count=1,flags=re.S)
if n!=1: raise SystemExit('directGaugeFor block missing')

helper=helper.replace('int keep=Math.min(420,overviewRivers.size());','int keep=Math.min(220,overviewRivers.size());',1)
helper=helper.replace('int keep=Math.min(64,candidates.size());chosen.addAll(candidates.subList(0,keep));','int keep=Math.min(40,candidates.size());chosen.addAll(candidates.subList(0,keep));',1)
helper=helper.replace('for(int i=0;i<Math.min(180,overviewRivers.size());i++)','for(int i=0;i<Math.min(90,overviewRivers.size());i++)',1)

rain_pat=r'''    private void refreshRainSources\(\) \{.*?\n    \}\n\n    private void refreshUserSource'''
rain_new=r'''    private void refreshRainSources() {
        if (!styleReady || style == null) return;
        double z=(map==null?6.0:map.getCameraPosition().zoom);
        if(z<8.0){
            String e=emptyFeatureCollection();
            setGeo("fs-rain-stale",e);setGeo("fs-rain-normal",e);setGeo("fs-rain-alert",e);setGeo("fs-rain-warning",e);setGeo("fs-rain-danger",e);
            return;
        }
        List<RainDot> snapshot; synchronized (rainStations) { snapshot = new ArrayList<>(rainStations); }
        setGeo("fs-rain-stale", rainGeo(snapshot, "stale"));
        setGeo("fs-rain-normal", rainGeo(snapshot, "normal"));
        setGeo("fs-rain-alert", rainGeo(snapshot, "alert"));
        setGeo("fs-rain-warning", rainGeo(snapshot, "warning"));
        setGeo("fs-rain-danger", rainGeo(snapshot, "danger"));
    }

    private void refreshUserSource'''
helper,n=re.subn(rain_pat,rain_new,helper,count=1,flags=re.S)
if n!=1: raise SystemExit('refreshRainSources block missing')

helper=helper.replace('int n=Math.min(30,visibleSnapshot.size());','int n=Math.min(42,visibleSnapshot.size());',1)
helper=helper.replace('%6000L)/6000.0','%5200L)/5200.0',1)

map_path.write_text(helper,encoding='utf-8')

gradle=gradle.replace('versionCode 37','versionCode 38',1).replace("versionName '0.8.17'","versionName '0.8.18'",1)
if 'versionCode 38' not in gradle or "versionName '0.8.18'" not in gradle: raise SystemExit('version bump failed')
gradle_path.write_text(gradle,encoding='utf-8')

h=map_path.read_text(encoding='utf-8')
for marker in ['अर्को नदी/खोलाको gauge reference यहाँ देखाइँदैन','if(s==null||!s.fresh','Math.min(220,overviewRivers.size())','Math.min(40,candidates.size())','if(z<8.0)','Math.min(42,visibleSnapshot.size())']:
    if marker not in h: raise SystemExit('v0.8.18 marker missing: '+marker)
if 'नजिकको gauge reference मात्र' in h: raise SystemExit('nearest-river reference still present')
print('FloodSafe v0.8.18 exact same-river + clean web map PASS')
