from pathlib import Path

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
m=p.read_text(encoding='utf-8')
anchor='    private static String formatOfficialTime(long at)'
pos=m.find(anchor)
if pos<0: raise SystemExit('formatOfficialTime anchor missing')

helpers=''
if 'private StationDot directGaugeFor(RiverWay r,double la,double lo)' not in m:
    helpers += '''    private StationDot directGaugeFor(RiverWay r,double la,double lo){return sameRiverGaugeFor(r,la,lo,true);}\n\n'''
if 'private static String riverMatchKey(RiverWay r)' not in m:
    helpers += '''    private static String riverMatchKey(RiverWay r){\n        if(r==null)return "";String k=riverNameKey(r.matchName);return k.length()>=3?k:riverNameKey(r.name);\n    }\n'''
if 'private static boolean sameRiverKey(String a,String b)' not in m:
    helpers += '''    private static boolean sameRiverKey(String a,String b){\n        if(a==null||b==null||a.length()<3||b.length()<3)return false;\n        if(a.equals(b))return true;\n        // Well-known local aliases: official DHM/BIPAD and OSM sometimes use different names.\n        if((a.contains("dhobi")||a.contains("rudramati"))&&(b.contains("dhobi")||b.contains("rudramati")))return true;\n        return false;\n    }\n'''
if 'private static String riverNameKey(String s)' not in m:
    helpers += r'''    private static String riverNameKey(String s){
        if(s==null)return "";
        String x=s.toLowerCase(Locale.ROOT)
                .replace('&',' ')
                .replaceAll("\\([^)]*\\)"," ")
                .replaceAll("\\b(at|near|beside|upstream|downstream)\\b.*$"," ")
                .replaceAll("\\b(river|khola|kholaa|nadi|nadhi|stream|station|gauge|hydrological|hydro|hs|bridge|highway|barrage)\\b"," ")
                .replaceAll("[^a-z0-9]"," ").replaceAll("\\s+"," ").trim();
        return x.replace(" ","");
    }
'''

if helpers:
    m=m[:pos]+helpers+'\n'+m[pos:]

for marker in ['private StationDot directGaugeFor','private static String riverMatchKey','private static boolean sameRiverKey','private static String riverNameKey']:
    if marker not in m: raise SystemExit('helper restore failed: '+marker)
p.write_text(m,encoding='utf-8')
print('v0.8.25 river helper restore PASS')
