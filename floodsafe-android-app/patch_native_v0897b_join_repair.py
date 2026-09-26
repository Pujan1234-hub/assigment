from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
l_path=src/'FloodLiveGaugeMonitor.java'
a=a_path.read_text(encoding='utf-8')
l=l_path.read_text(encoding='utf-8')

# Avoid Java illegal-forward-reference: use the direct official URL literally.
old='private static final String RIVER_ENDPOINT=BIPAD+"river/?limit=5000"; // V0897_DIRECT_BIPAD_BACKGROUND'
new='private static final String RIVER_ENDPOINT="https://bipadportal.gov.np/api/v1/river/?limit=5000"; // V0897B_DIRECT_BIPAD_BACKGROUND_LITERAL'
if old not in l: raise SystemExit('v0897b monitor URL anchor missing')
l=l.replace(old,new,1)

# Robust current-row join: exact station id -> exact normalized station name -> nearest
# official catalog coordinate. This prevents BIPAD schema/name drift from zeroing readings.
anchor='    } // V0897_BIPAD_TIME_PARSER\n'
if anchor not in a: raise SystemExit('v0897b time helper anchor missing')
helper=r'''

    private static double v897bKm(double a,double b,double c,double d){
        double R=6371d,dp=Math.toRadians(c-a),dl=Math.toRadians(d-b);
        double q=Math.sin(dp/2d)*Math.sin(dp/2d)+Math.cos(Math.toRadians(a))*Math.cos(Math.toRadians(c))*Math.sin(dl/2d)*Math.sin(dl/2d);
        return 2d*R*Math.asin(Math.min(1d,Math.sqrt(q)));
    }

    private JSONObject v897bMatchCatalog(JSONObject live,java.util.LinkedHashMap<String,JSONObject> byIndex,java.util.LinkedHashMap<String,JSONObject> byName,JSONArray catalog){
        if(live==null)return null;
        String ix=v846StationIndex(live),nm=v846StationName(live);
        JSONObject meta=!ix.isEmpty()?byIndex.get(v846Key(ix)):null;
        if(meta==null&&!nm.isEmpty())meta=byName.get(v846Key(nm));
        if(meta!=null)return meta;
        double[] p=v870OfficialCoord(live);
        if(!Double.isFinite(p[0])||!Double.isFinite(p[1]))return null;
        JSONObject best=null;double bd=Double.POSITIVE_INFINITY;
        for(int i=0;i<catalog.length();i++){
            JSONObject c=catalog.optJSONObject(i);if(c==null)continue;
            double[] q=v870OfficialCoord(c);if(!Double.isFinite(q[0])||!Double.isFinite(q[1]))continue;
            double d=v897bKm(p[0],p[1],q[0],q[1]);if(d<bd){bd=d;best=c;}
        }
        return bd<=2.5d?best:null;
    } // V0897B_ID_NAME_COORDINATE_FALLBACK
'''
a=a.replace(anchor,anchor+helper,1)

old_block='''                    String ix=v846StationIndex(live),nm=v846StationName(live);\n                    JSONObject meta=!ix.isEmpty()?metaByIndex.get(v846Key(ix)):null;\n                    if(meta==null&&!nm.isEmpty())meta=metaByName.get(v846Key(nm));\n                    if(meta==null)continue;'''
new_block='''                    JSONObject meta=v897bMatchCatalog(live,metaByIndex,metaByName,catalog); // V0897B_CURRENT_ROW_ROBUST_JOIN\n                    if(meta==null)continue;'''
if old_block not in a: raise SystemExit('v0897b live join block missing')
a=a.replace(old_block,new_block,1)

for x in ('V0897B_DIRECT_BIPAD_BACKGROUND_LITERAL','V0897B_ID_NAME_COORDINATE_FALLBACK','V0897B_CURRENT_ROW_ROBUST_JOIN'):
    if x not in a+l: raise SystemExit('missing '+x)

a_path.write_text(a,encoding='utf-8')
l_path.write_text(l,encoding='utf-8')
print('v0.8.97b robust BIPAD join and background URL compile repair applied')
