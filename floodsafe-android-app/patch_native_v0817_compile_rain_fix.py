from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
m_path=src/'FloodSafeNativeMapView.java'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')

# Restore helper lost during later patch replacements.
if 'private void updateMapHintCounts()' not in a:
    anchor='    private void refreshRainUi(){'
    helper='''    private void updateMapHintCounts(){\n        if(mapHint==null)return;\n        mapHint.setText(t("🌊 current official "+mapRiverCurrent+" / "+mapRiverTotal+" • 🌧️ rain latest "+mapRainFresh+" / "+mapRainTotal,\n                          "🌊 current official "+mapRiverCurrent+" / "+mapRiverTotal+" • 🌧️ rain latest "+mapRainFresh+" / "+mapRainTotal));\n    }\n\n'''
    if anchor not in a: raise SystemExit('refreshRainUi anchor missing')
    a=a.replace(anchor,helper+anchor,1)

# BIPAD rain-stations latest feed stores rainfall in averages[] by interval.
if 'private static double rainAverage(JSONObject r,int interval)' not in a:
    anchor='    private RainStation parseRainStation(JSONObject r,long now){'
    helper=r'''    private static double rainAverage(JSONObject r,int interval){
        if(r==null)return Double.NaN; JSONArray av=r.optJSONArray("averages");
        if(av==null){JSONObject f=r.optJSONObject("fields");if(f!=null)av=f.optJSONArray("averages");}
        if(av!=null)for(int i=0;i<av.length();i++){JSONObject x=av.optJSONObject(i);if(x!=null&&x.optInt("interval",-1)==interval){double v=x.optDouble("value",Double.NaN);if(Double.isFinite(v))return v;}}
        return Double.NaN;
    }

'''
    if anchor not in a: raise SystemExit('rain parse anchor missing')
    a=a.replace(anchor,helper+anchor,1)

old='''        double mm=numDeep(r,f,"_lastRainfall","lastRainfall","rainfall","rainFall","rain","rainfall24h","rainfall_24h","currentRainfall","lastValue","_lastValue","value");'''
new='''        double mm1=rainAverage(r,1),mm3=rainAverage(r,3),mm6=rainAverage(r,6),mm12=rainAverage(r,12),mm24=rainAverage(r,24);\n        double mm=Double.isFinite(mm1)?mm1:numDeep(r,f,"_lastRainfall","lastRainfall","rainfall","rainFall","rain","rainfall24h","rainfall_24h","currentRainfall","lastValue","_lastValue","value");'''
if old in a:
    a=a.replace(old,new,1)
elif 'mm1=rainAverage(r,1)' not in a:
    raise SystemExit('rainfall parse line missing')

a=a.replace('return new RainStation(name,basin,a,o,mm,at,fresh,band,raw);',
            'return new RainStation(name,basin,a,o,mm,mm3,mm6,mm12,mm24,at,fresh,band,raw);',1)

pat=r'''    private static final class RainStation\{final String name,basin,band,rawStatus;final double lat,lon,rainfall;final long at;final boolean fresh;RainStation\(String n,String b,double a,double o,double mm,long tm,boolean f,String bd,String rs\)\{name=n;basin=b;lat=a;lon=o;rainfall=mm;at=tm;fresh=f;band=bd;rawStatus=rs;\}\}'''
rep='''    private static final class RainStation{final String name,basin,band,rawStatus;final double lat,lon,rainfall,rain3,rain6,rain12,rain24;final long at;final boolean fresh;RainStation(String n,String b,double a,double o,double mm,double m3,double m6,double m12,double m24,long tm,boolean f,String bd,String rs){name=n;basin=b;lat=a;lon=o;rainfall=mm;rain3=m3;rain6=m6;rain12=m12;rain24=m24;at=tm;fresh=f;band=bd;rawStatus=rs;}}'''
a,n=re.subn(pat,rep,a,count=1)
if n!=1 and 'rain3,rain6,rain12,rain24' not in a: raise SystemExit('RainStation class replacement failed')

# Native RainDot carries the official interval values into the tap detail sheet.
read_pat=r'''    private RainDot readRain\(Object o\)\{.*?\}\n    private static long getLong'''
read_new=r'''    private RainDot readRain(Object o){if(o==null)return null;try{Class<?> c=o.getClass();RainDot r=new RainDot();r.lat=getDouble(c,o,"lat");r.lon=getDouble(c,o,"lon");if(!Double.isFinite(r.lat)||!Double.isFinite(r.lon))return null;r.name=getString(c,o,"name","Official rain station");r.basin=getString(c,o,"basin","");r.band=getString(c,o,"band","stale");r.rawStatus=getString(c,o,"rawStatus","");r.fresh=getBoolean(c,o,"fresh",false);r.rainfall=getDouble(c,o,"rainfall");r.rain3=getDouble(c,o,"rain3");r.rain6=getDouble(c,o,"rain6");r.rain12=getDouble(c,o,"rain12");r.rain24=getDouble(c,o,"rain24");r.at=getLong(c,o,"at",-1L);return r;}catch(Exception e){return null;}}
    private static long getLong'''
m,n=re.subn(read_pat,read_new,m,count=1,flags=re.S)
if n!=1: raise SystemExit('readRain replacement failed')

show_pat=r'''    private void showRain\(RainDot r\)\{.*?\}\n'''
show_new=r'''    private void showRain(RainDot r){StringBuilder x=new StringBuilder();x.append("BIPAD/DHM official rain station");if(r.basin!=null&&!r.basin.isEmpty())x.append("\nBasin: ").append(r.basin);if(Double.isFinite(r.rainfall))x.append(String.format(Locale.US,"\nRain 1h: %.1f mm",r.rainfall));if(Double.isFinite(r.rain3))x.append(String.format(Locale.US,"\nRain 3h: %.1f mm",r.rain3));if(Double.isFinite(r.rain6))x.append(String.format(Locale.US,"\nRain 6h: %.1f mm",r.rain6));if(Double.isFinite(r.rain12))x.append(String.format(Locale.US,"\nRain 12h: %.1f mm",r.rain12));if(Double.isFinite(r.rain24))x.append(String.format(Locale.US,"\nRain 24h: %.1f mm",r.rain24));x.append("\nReading: ").append(r.fresh?"LATEST":"STALE / OLD");x.append("\nOfficial time: ").append(formatOfficialTime(r.at));if(r.rawStatus!=null&&!r.rawStatus.isEmpty())x.append("\nSource status: ").append(r.rawStatus);new AlertDialog.Builder(getContext()).setTitle("🌧️ "+r.name).setMessage(x.toString()).setPositiveButton("ठीक छ",null).show();}
'''
m,n=re.subn(show_pat,show_new,m,count=1,flags=re.S)
if n!=1: raise SystemExit('showRain replacement failed')

m=m.replace('private static final class RainDot { String name,basin,band,rawStatus; double lat,lon,rainfall; long at; boolean fresh; }',
            'private static final class RainDot { String name,basin,band,rawStatus; double lat,lon,rainfall,rain3,rain6,rain12,rain24; long at; boolean fresh; }',1)
if 'rainfall,rain3,rain6,rain12,rain24' not in m: raise SystemExit('RainDot interval fields missing')

a_path.write_text(a,encoding='utf-8')
m_path.write_text(m,encoding='utf-8')

for marker in ['private void updateMapHintCounts()','rainAverage(JSONObject r,int interval)','rain3,rain6,rain12,rain24']:
    if marker not in a: raise SystemExit('activity compile/rain marker missing: '+marker)
for marker in ['Rain 1h:','Rain 24h:','rainfall,rain3,rain6,rain12,rain24']:
    if marker not in m: raise SystemExit('map rain detail marker missing: '+marker)
print('FloodSafe v0.8.17 compile + official rain interval detail fix PASS')
