from pathlib import Path
import re

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
a=a_path.read_text(encoding='utf-8')

# Final live-display guard:
# - only official readings <=20 minutes old enter the active river/station UI
# - when the official source has no <=20m reading, clear previous live rows instead of retaining old data
# - never show hour/day-old age text as current/live information
# Source polling remains 10 seconds; this does not invent measurements.

def method_span(text,name,ret='void'):
    m=re.search(r'(?m)^\s*private\s+'+re.escape(ret)+r'\s+'+re.escape(name)+r'\s*\([^)]*\)\s*\{',text)
    if not m:return None
    op=text.find('{',m.start());depth=0;quote=None;esc=False
    i=op
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
                if depth==0:return (m.start(),i+1)
        i+=1
    return None

refresh=r'''    private void refreshRivers(){
        if(v862FinalRefreshInFlight)return;v862FinalRefreshInFlight=true;
        io.execute(()->{
            try{
                long now=System.currentTimeMillis();List<RiverStation> out=loadTrustedRiverStationsV862(now);
                out.removeIf(s->s==null||!s.fresh); // V0862_FRESH20_LIVE_ONLY
                out.sort(Comparator.comparingInt((RiverStation s)->s.rank).thenComparing(s->s.name,String.CASE_INSENSITIVE_ORDER));
                String fp=v862FinalFingerprint(out);boolean changed=!fp.equals(v862FinalLastFingerprint);
                if(changed){synchronized(stations){stations.clear();stations.addAll(out);}v862FinalLastFingerprint=fp;}
                runOnUiThread(()->{v862FinalRefreshInFlight=false;if(changed)refreshRiverUi();});
            }catch(Exception e){runOnUiThread(()->v862FinalRefreshInFlight=false);}
        });
    } // V0862_FINAL_NO_FLICKER_REFRESH V0862_FRESH20_CLEAR_STALE
'''
sp=method_span(a,'refreshRivers','void')
if not sp:raise SystemExit('fresh20 refreshRivers anchor missing')
a=a[:sp[0]]+refresh+a[sp[1]:]

line=r'''    private String stationLine(RiverStation s){
        if(s==null||!s.fresh)return t("पछिल्लो २० मिनेटमा नयाँ आधिकारिक मापन छैन","No new official reading in the last 20 min");
        String lev=Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):t("सतह उपलब्ध छैन","level unavailable");
        long min=s.at>0?Math.max(0,(System.currentTimeMillis()-s.at)/60000L):0;
        String age=t(min+" मिनेटअघि",min+" min ago");
        double km=distanceKm(s.lat,s.lon);String dist=Double.isFinite(km)?String.format(Locale.US," • %.1f km",km):"";
        return stageName(s.stage)+" • "+lev+" • "+age+dist;
    } // V0862_FRESH20_STATION_LINE
'''
sp=method_span(a,'stationLine','String')
if not sp:raise SystemExit('fresh20 stationLine anchor missing')
a=a[:sp[0]]+line+a[sp[1]:]

detail=r'''    private void showStation(RiverStation s){
        if(s==null)return;
        if(!s.fresh){
            new AlertDialog.Builder(this).setTitle(s.name).setMessage(t(
                    "पछिल्लो २० मिनेटमा नयाँ आधिकारिक पानी-सतह मापन उपलब्ध छैन। पुरानो घण्टा/दिनअघिको मापनलाई LIVE भनेर देखाइँदैन।",
                    "No new official water-level reading is available in the last 20 minutes. Hour/day-old readings are not shown as LIVE."))
                    .setPositiveButton(t("ठीक छ","OK"),null).show();return;
        }
        StringBuilder b=new StringBuilder();
        b.append(v0857StatusDot(s)).append(" ").append(stageName(s.stage));
        if(Double.isFinite(s.level))b.append("\n\n").append(t("पानीको सतह: ","Water level: ")).append(String.format(Locale.US,"%.2f m",s.level));
        if(s.at>0){long min=Math.max(0,(System.currentTimeMillis()-s.at)/60000L);b.append("\n").append(t("मापन: ","Measured: ")).append(min).append(t(" मिनेटअघि"," min ago"));}
        if(Double.isFinite(s.warning))b.append("\n").append(t("चेतावनी तह: ","Warning level: ")).append(String.format(Locale.US,"%.2f m",s.warning));
        if(Double.isFinite(s.danger))b.append("\n").append(t("खतरा तह: ","Danger level: ")).append(String.format(Locale.US,"%.2f m",s.danger));
        b.append("\n\n").append(t("स्रोत: BIPAD/DHM आधिकारिक नदी मापन • LIVE window २० मिनेट","Source: official BIPAD/DHM river measurement • 20-minute LIVE window"));
        new AlertDialog.Builder(this).setTitle(s.name).setMessage(b.toString()).setPositiveButton(t("ठीक छ","OK"),null).show();
    } // V0862_FRESH20_STATION_DETAIL
'''
sp=method_span(a,'showStation','void')
if not sp:raise SystemExit('fresh20 showStation anchor missing')
a=a[:sp[0]]+detail+a[sp[1]:]

for marker in ['V0862_FRESH20_LIVE_ONLY','V0862_FRESH20_CLEAR_STALE','V0862_FRESH20_STATION_LINE','V0862_FRESH20_STATION_DETAIL','main.postDelayed(this,10_000L);','RIVER_FRESH_MS=20L*60L*1000L']:
    if marker not in a:raise SystemExit('fresh20 verification failed: '+marker)

# The live collection must be able to become empty; otherwise an old reading could remain visible forever.
if 'if(changed){synchronized(stations){stations.clear();stations.addAll(out);}' not in a:
    raise SystemExit('fresh20 stale-clear guard missing')

a_path.write_text(a,encoding='utf-8')
print('FloodSafe v0.8.62 PASS: active UI is official <=20-minute readings only; stale hour/day readings are cleared, not retained')
