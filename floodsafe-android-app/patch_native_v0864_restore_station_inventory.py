from pathlib import Path

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.64: restore station inventory on the native map without weakening live safety.
# Regression cause: v0.8.62 proxy fallback cleared the already-loaded BIPAD catalog
# before it knew whether the proxy returned any usable river rows. If latest/current
# was empty, a successful-but-empty proxy response reduced the whole map to 0 stations.
# Keep official catalog positions visible; proxy/current rows may enrich/override them.
# Freshness (<=20 min), 2 km warning/danger alerts, river-tap same-river truth unchanged.

old='''        if(current.isEmpty()){
            try{
                JSONArray rr=rows(getJson(RIVER_ENDPOINT+"?_nativefull="+now+"&_nocache="+System.nanoTime()));out.clear();
                for(int i=0;i<rr.length();i++){JSONObject r=rr.optJSONObject(i);if(r==null)continue;try{r.put("_floodsafeOnline",true);r.put("_floodsafeSource","official proxy fallback");}catch(Exception ignored){}RiverStation s=parseStation(r,now);if(s!=null)out.add(s);}
                v849LatestCount=out.size();if(v849CatalogCount<=0)v849CatalogCount=out.size();
            }catch(Exception ignored){}
        }
'''
new='''        if(current.isEmpty()){
            try{
                JSONArray rr=rows(getJson(RIVER_ENDPOINT+"?_nativefull="+now+"&_nocache="+System.nanoTime()));
                List<RiverStation> proxyRows=new ArrayList<>();
                for(int i=0;i<rr.length();i++){JSONObject r=rr.optJSONObject(i);if(r==null)continue;try{r.put("_floodsafeOnline",true);r.put("_floodsafeSource","official proxy fallback");}catch(Exception ignored){}RiverStation s=parseStation(r,now);if(s!=null)proxyRows.add(s);}
                // Never clear the catalog just because a fallback endpoint is empty.
                // This keeps official station positions on the map even when there is no
                // current <=20-minute observation. Proxy rows only override matching
                // catalog entries when they actually exist.
                if(!proxyRows.isEmpty()){out.addAll(proxyRows);out=v864PreferCurrentStation(out);v849LatestCount=proxyRows.size();}
                if(v849CatalogCount<=0&& !out.isEmpty())v849CatalogCount=out.size();
            }catch(Exception ignored){}
        } // V0864_NEVER_CLEAR_STATION_INVENTORY
'''
if old not in a:
    raise SystemExit('v0864 proxy-clear regression anchor missing')
a=a.replace(old,new,1)

helper='''    private static List<RiverStation> v864PreferCurrentStation(List<RiverStation> in){
        java.util.LinkedHashMap<String,RiverStation> m=new java.util.LinkedHashMap<>();
        for(RiverStation s:in){
            if(s==null)continue;
            String k=(s.name==null?"":s.name.toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9]+",""))+String.format(Locale.US,"|%.4f|%.4f",s.lat,s.lon);
            RiverStation old=m.get(k);
            if(old==null || (s.fresh&&!old.fresh) || (s.online&&!old.online))m.put(k,s);
        }
        return new ArrayList<>(m.values());
    } // V0864_PROXY_OVERLAYS_CATALOG

'''
anchor='    private static String v862FinalKey('
if anchor not in a:raise SystemExit('v0864 helper anchor missing')
a=a.replace(anchor,helper+anchor,1)

# Version only. Do not touch river rendering/tap logic or safety windows.
if 'versionCode 83' in g:g=g.replace('versionCode 83','versionCode 84',1)
elif 'versionCode 84' not in g:raise SystemExit('v0864 versionCode anchor missing')
if "versionName '0.8.63'" in g:g=g.replace("versionName '0.8.63'","versionName '0.8.64'",1)
elif "versionName '0.8.64'" not in g:raise SystemExit('v0864 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

for x in ['V0864_NEVER_CLEAR_STATION_INVENTORY','V0864_PROXY_OVERLAYS_CATALOG','V0862_FINAL_TRUE_REALTIME_BIPAD_DHM','V0857_DISTRICT_FRESH_WATERLEVEL_ONLY','RIVER_FRESH_MS=20L*60L*1000L']:
    if x not in a:raise SystemExit('v0864 activity guard failed: '+x)
if 'out.clear();' in a[a.find('private List<RiverStation> loadTrustedRiverStationsV862'):a.find('private RiverStation parseStation',a.find('private List<RiverStation> loadTrustedRiverStationsV862'))]:
    raise SystemExit('v0864 destructive station clear still present in final loader')
for x in ['versionCode 84',"versionName '0.8.64'"]:
    if x not in g:raise SystemExit('v0864 version guard failed: '+x)
print('FloodSafe v0.8.64 PASS: station inventory retained; empty proxy can no longer erase map stations; 20m safety unchanged')
