from pathlib import Path

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
s=p.read_text(encoding='utf-8')
start=s.find('    private void showRain(RainDot r){')
end=s.find('    private void startParticles() {',start)
if start<0 or end<0: raise SystemExit('showRain anchors missing')
block=r'''    private void showRain(RainDot r){
        StringBuilder x=new StringBuilder();
        x.append("BIPAD/DHM official rain station");
        if(r.basin!=null&&!r.basin.isEmpty())x.append("\\nBasin: ").append(r.basin);
        if(Double.isFinite(r.rainfall))x.append(String.format(Locale.US,"\\nRain 1h: %.1f mm",r.rainfall));
        if(Double.isFinite(r.rain3))x.append(String.format(Locale.US,"\\nRain 3h: %.1f mm",r.rain3));
        if(Double.isFinite(r.rain6))x.append(String.format(Locale.US,"\\nRain 6h: %.1f mm",r.rain6));
        if(Double.isFinite(r.rain12))x.append(String.format(Locale.US,"\\nRain 12h: %.1f mm",r.rain12));
        if(Double.isFinite(r.rain24))x.append(String.format(Locale.US,"\\nRain 24h: %.1f mm",r.rain24));
        x.append("\\nReading: ").append(r.fresh?"LATEST":"STALE / OLD");
        x.append("\\nOfficial time: ").append(formatOfficialTime(r.at));
        if(r.rawStatus!=null&&!r.rawStatus.isEmpty())x.append("\\nSource status: ").append(r.rawStatus);
        new AlertDialog.Builder(getContext()).setTitle("Rain • "+r.name).setMessage(x.toString()).setPositiveButton("ठीक छ",null).show();
    }

'''
s=s[:start]+block+s[end:]
p.write_text(s,encoding='utf-8')
q=p.read_text(encoding='utf-8')
for m in ['\\\\nRain 1h:','\\\\nRain 24h:','setTitle("Rain • "+r.name)']:
    if m not in q: raise SystemExit('rain string fix marker missing: '+m)
print('FloodSafe v0.8.17 rain Java string escaping PASS')
