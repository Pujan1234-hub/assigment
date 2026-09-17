from pathlib import Path
import re

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
a=p.read_text(encoding='utf-8')

# v0.8.48 compile repair:
# Earlier station-inventory patch inserted the catalog loop at the last `return out;`
# before trustedPages(), which can be v846ParseDhmRows(). Move it strictly inside
# loadTrustedRiverStations(), then restore tiny display helpers referenced by station detail.

catalog_block=r'''        for(int i=0;i<catalog.length();i++){
            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;
            String ix=v846StationIndex(c),nm=v846StationName(c);
            String key=!ix.isEmpty()?"i:"+v846Key(ix):"n:"+v846Key(nm);
            if(liveKeys.contains(key))continue;
            try{c.put("_floodsafeCatalogOnly",true);}catch(Exception ignored){}
            RiverStation s=parseStation(c,now);if(s!=null)out.add(s);
        }
        out=v848DedupStations(out);
'''

# Remove every existing copy first so a misplaced copy can never compile in a helper.
a=a.replace(catalog_block,'')

ls=a.find('    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{')
le=a.find('    private static String v846StationIndex(',ls)
if ls<0 or le<0:
    raise SystemExit('v0.8.48 compile fix loader anchors missing')
loader=a[ls:le]
if 'V0848_ALL_OFFICIAL_STATIONS' not in loader or 'JSONArray catalog=' not in loader or 'liveKeys' not in loader:
    raise SystemExit('v0.8.48 compile fix station inventory prerequisites missing')
ret=loader.rfind('        return out;')
if ret<0:
    raise SystemExit('v0.8.48 compile fix loader return missing')
loader=loader[:ret]+catalog_block+loader[ret:]
a=a[:ls]+loader+a[le:]

# Detail helpers referenced by the current combined station/rain detail UI.
if 'private static String mapDisplayStage(RiverStation s)' not in a:
    helper=r'''    private static String mapDisplayStage(RiverStation s){
        if(s==null||!s.fresh)return "stale";
        String z=s.stage==null?"":s.stage.trim().toLowerCase(Locale.ROOT);
        return z.isEmpty()?"unknown":z;
    }
    private static String mapReadingAge(long at){
        if(at<=0)return "unknown";
        long min=Math.max(0L,(System.currentTimeMillis()-at)/60000L);
        if(min<60)return min+" min";
        long h=min/60L;if(h<48)return h+" h";
        return (h/24L)+" d";
    }

'''
    anchor='    private void showStation('
    if anchor not in a:
        raise SystemExit('v0.8.48 compile fix showStation anchor missing')
    a=a.replace(anchor,helper+anchor,1)

# Hard checks: catalog loop must exist exactly once and only inside official loader.
if a.count('_floodsafeCatalogOnly')!=1:
    raise SystemExit('v0.8.48 catalog loop count invalid: '+str(a.count('_floodsafeCatalogOnly')))
ls=a.find('    private List<RiverStation> loadTrustedRiverStations(long now)throws Exception{')
le=a.find('    private static String v846StationIndex(',ls)
loader=a[ls:le]
for marker in ['_floodsafeCatalogOnly','v848DedupStations(out)','V0848_ALL_OFFICIAL_STATIONS','mapDisplayStage','mapReadingAge']:
    if marker not in (loader if marker in ['_floodsafeCatalogOnly','v848DedupStations(out)','V0848_ALL_OFFICIAL_STATIONS'] else a):
        raise SystemExit('v0.8.48 compile marker missing: '+marker)

p.write_text(a,encoding='utf-8')
print('FloodSafe v0.8.48 compile repair PASS: catalog loop scoped to official loader')
