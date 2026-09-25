from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')

# River-only clean map:
# - rainfall measurements stay loaded in memory but rain-station markers/click targets never render
# - river tap shows the same-river BIPAD reading plus nearest relevant official rainfall in one card
# - flow/glow remains limited to current official same-river segments from v0.8.25

# Force all rain point sources empty at every zoom. Rain data remains available for river detail.
rs=m.find('    private void refreshRainSources() {')
re_=m.find('    private void refreshUserSource() {',rs)
if rs<0 or re_<0:
    raise SystemExit('refreshRainSources anchors missing')
rain_block=r'''    private void refreshRainSources() {
        if(!styleReady||style==null)return;
        String e=emptyFeatureCollection();
        setGeo("fs-rain-stale",e);
        setGeo("fs-rain-normal",e);
        setGeo("fs-rain-alert",e);
        setGeo("fs-rain-warning",e);
        setGeo("fs-rain-danger",e);
    }

'''
m=m[:rs]+rain_block+m[re_:]

# River click card: source-separated river + rainfall truth in a single panel.
ss=m.find('    private void showRiver(')
se=m.find('    private StationDot sameRiverGaugeFor(',ss)
if ss<0 or se<0:
    raise SystemExit('showRiver/sameRiverGaugeFor anchors missing')
show_block=r'''    private void showRiver(RiverWay r,double la,double lo) {
        StationDot current=sameRiverGaugeFor(r,la,lo,true);
        StationDot known=current!=null?current:sameRiverGaugeFor(r,la,lo,false);
        double refLat=current!=null?current.lat:la,refLon=current!=null?current.lon:lo;
        RainDot rain=nearestRainForRiver(refLat,refLon);
        String title=(r==null||r.name==null||r.name.trim().isEmpty()||"नदी / खोला".equals(r.name))?"नदी / खोला":r.name;
        StringBuilder x=new StringBuilder();
        x.append("🌊 BIPAD official river detail");
        if(current!=null){
            x.append("\nGauge: ").append(current.name).append(String.format(Locale.US," • %.1f km",km(la,lo,current.lat,current.lon)));
            if(Double.isFinite(current.level))x.append(String.format(Locale.US,"\nWater level: %.2f m",current.level));
            if(Double.isFinite(current.warning))x.append(String.format(Locale.US,"\nWarning level: %.2f m",current.warning));
            if(Double.isFinite(current.danger))x.append(String.format(Locale.US,"\nDanger level: %.2f m",current.danger));
            String source=current.rawStatus==null?"":current.rawStatus.trim();
            x.append("\nSource status: ").append(source.isEmpty()?current.stage.toUpperCase(Locale.ROOT):source);
            x.append("\nOfficial time: ").append(formatOfficialTime(current.at));
        }else if(known!=null){
            x.append("\nयसै नदी/खोलाको BIPAD gauge छ, तर current official reading उपलब्ध छैन।")
             .append("\nGauge: ").append(known.name)
             .append("\nStatus: STALE / UNKNOWN")
             .append("\nOfficial time: ").append(formatOfficialTime(known.at));
        }else{
            x.append("\nयो नदी/खोलामा matching BIPAD official gauge भेटिएन।")
             .append("\nअर्को नदीको nearest gauge reference देखाइँदैन।");
        }

        x.append("\n\n🌧️ DHM official rainfall detail");
        if(rain!=null){
            double rd=km(refLat,refLon,rain.lat,rain.lon);
            x.append("\nRain station: ").append(rain.name).append(String.format(Locale.US," • %.1f km",rd));
            if(rain.basin!=null&&!rain.basin.trim().isEmpty())x.append("\nBasin: ").append(rain.basin.trim());
            if(Double.isFinite(rain.rainfall))x.append(String.format(Locale.US,"\nRain 1h: %.1f mm",rain.rainfall));
            if(Double.isFinite(rain.rain3))x.append(String.format(Locale.US,"\nRain 3h: %.1f mm",rain.rain3));
            if(Double.isFinite(rain.rain6))x.append(String.format(Locale.US,"\nRain 6h: %.1f mm",rain.rain6));
            if(Double.isFinite(rain.rain12))x.append(String.format(Locale.US,"\nRain 12h: %.1f mm",rain.rain12));
            if(Double.isFinite(rain.rain24))x.append(String.format(Locale.US,"\nRain 24h: %.1f mm",rain.rain24));
            x.append("\nRain reading: ").append(rain.fresh?"LATEST":"STALE / OLD");
            x.append("\nRain official time: ").append(formatOfficialTime(rain.at));
            if(rain.rawStatus!=null&&!rain.rawStatus.trim().isEmpty())x.append("\nRain source status: ").append(rain.rawStatus.trim());
        }else{
            x.append("\nयस नदी नजिक usable official rainfall reading भेटिएन।");
        }
        x.append("\n\nRiver source: BIPAD official");
        x.append("\nRainfall source: DHM official rainfall feed");
        x.append("\nRain stations are hidden from the map for a clean river-only view.");
        if(stationTapListener!=null){stationTapListener.onStationTap(new RiverTapInfo(title,x.toString()));return;}
        new AlertDialog.Builder(getContext()).setTitle(title).setMessage(x.toString()).setPositiveButton("ठीक छ",null).show();
    }

    private RainDot nearestRainForRiver(double la,double lo){
        RainDot freshBest=null,anyBest=null;double freshD=Double.MAX_VALUE,anyD=Double.MAX_VALUE;
        synchronized(rainStations){
            for(RainDot rr:rainStations){
                if(rr==null)continue;
                double d=km(la,lo,rr.lat,rr.lon);
                if(d<anyD){anyD=d;anyBest=rr;}
                if(rr.fresh&&d<freshD){freshD=d;freshBest=rr;}
            }
        }
        if(freshBest!=null&&freshD<=60.0)return freshBest;
        if(anyBest!=null&&anyD<=40.0)return anyBest;
        return null;
    }

'''
m=m[:ss]+show_block+m[se:]

# Keep river interaction first and make sure hidden rain dots never steal a tap.
if 'showRain(nearestRain)' in m:
    raise SystemExit('rain marker click target remained after river-only patch')

# Source wording in the in-map white detail card must stay separated.
a=a.replace(
    'BIPAD / DHM official source • stale data लाई live खतरा मानिँदैन।',
    'River: BIPAD official • Rainfall: DHM official • stale data लाई live खतरा मानिँदैन।',1)
a=a.replace(
    'BIPAD / DHM official source • stale data is never treated as a live threat.',
    'River: BIPAD official • Rainfall: DHM official • stale data is never treated as a live threat.',1)

# Clear map subtitle: rain measurements are in the river detail card, not as map markers.
a,n=re.subn(
    r'mapSub\.setText\(t\("[^"]*","[^"]*"\)\);',
    'mapSub.setText(t("नेपालभित्र actual नदी • BIPAD data भएको नदीमा मात्र flow/glow • river tap मा BIPAD detail + DHM rainfall • rain marker छैन","Nepal-only actual rivers • flow/glow only where BIPAD has current data • river tap shows BIPAD detail + DHM rainfall • no rain markers"));',
    a,count=1)
if n!=1:
    raise SystemExit('map subtitle assignment missing')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')

# Hard gates: clean river-only map, combined detail card, and current-only flow contract.
a2=a_path.read_text(encoding='utf-8');m2=m_path.read_text(encoding='utf-8')
for marker in [
    'River: BIPAD official • Rainfall: DHM official',
    'BIPAD data भएको नदीमा मात्र flow/glow',
    'no rain markers']:
    if marker not in a2: raise SystemExit('v0.8.27 activity marker missing: '+marker)
for marker in [
    'setGeo("fs-rain-stale",e)','nearestRainForRiver','🌊 BIPAD official river detail',
    '🌧️ DHM official rainfall detail','Rain 1h:','Rain 24h:','currentFlowRivers',
    'stationTapListener.onStationTap(new RiverTapInfo']:
    if marker not in m2: raise SystemExit('v0.8.27 map marker missing: '+marker)
if 'showRain(nearestRain)' in m2: raise SystemExit('hidden rain marker click target remained')
if 'List<RiverWay> visibleSnapshot=new ArrayList<>(rivers);' in m2: raise SystemExit('all-river fake flow returned')
print('FloodSafe river-only map + combined BIPAD river/DHM rainfall detail PASS')
