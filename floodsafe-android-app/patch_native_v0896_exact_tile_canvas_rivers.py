from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
m_path=src/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:(?:private|public|protected)\s+)?[A-Za-z0-9_<>\[\]?., ]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
    if not q:return None
    op=text.find('{',q.start());d=0;quote=None;esc=False
    for i in range(op,len(text)):
        c=text[i]
        if quote:
            if esc:esc=False
            elif c=='\\':esc=True
            elif c==quote:quote=None
        else:
            if c in ('\"',"'"):quote=c
            elif c=='{':d+=1
            elif c=='}':
                d-=1
                if d==0:return q.start(),i+1
    return None

def replace_method(text,name,block):
    s=method_span(text,name)
    if not s: raise SystemExit('missing method '+name)
    return text[:s[0]]+block+text[s[1]:]

field='    private volatile String v894PendingFingerprint = ""; // V0894_RIVER_MATCH_DEBOUNCE'
if field not in m: raise SystemExit('v0894 field anchor missing')
m=m.replace(field,field+'\n    private V896RiverOverlay v896RiverOverlay; // V0896_GUARANTEED_CANVAS_RIVER_RENDER',1)

anchor='        addView(mapView, new LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT));'
if anchor not in m: raise SystemExit('mapView add anchor missing')
m=m.replace(anchor,anchor+'\n        v896RiverOverlay=new V896RiverOverlay(context);\n        addView(v896RiverOverlay,new LayoutParams(LayoutParams.MATCH_PARENT,LayoutParams.MATCH_PARENT));',1)

refresh=r'''    private void v893RefreshDedicatedStationRivers(){
        final List<StationDot> ss; synchronized(stations){ss=new ArrayList<>(stations);}
        if(ss.isEmpty())return;
        StringBuilder fb=new StringBuilder();
        for(StationDot s:ss)if(s!=null&&Double.isFinite(s.lat)&&Double.isFinite(s.lon))fb.append(v881Norm(s.name)).append('@').append(Math.round(s.lat*10000d)).append(',').append(Math.round(s.lon*10000d)).append(';');
        final String fingerprint=fb.toString();
        if(fingerprint.equals(v894StationGeometryFingerprint)&&!v893StationRivers.isEmpty()){
            v894UpdateDedicatedStatus(ss);if(v896RiverOverlay!=null)v896RiverOverlay.invalidate();return;
        }
        v894PendingFingerprint=fingerprint;
        if(v894RiverMatchRunning)return;
        v894RiverMatchRunning=true;
        io.execute(()->{
            try{
                java.util.LinkedHashSet<RiverWay> chosen=new java.util.LinkedHashSet<>();
                java.util.LinkedHashMap<String,List<RiverWay>> tileCache=new java.util.LinkedHashMap<>();
                for(StationDot s:ss){
                    if(s==null||!Double.isFinite(s.lat)||!Double.isFinite(s.lon))continue;
                    int cx=v879TileX(s.lon),cy=v879TileY(s.lat);List<RiverWay> local=new ArrayList<>();
                    for(int x=Math.max(0,cx-1);x<=Math.min(V879_TILE_NX-1,cx+1);x++)for(int y=Math.max(0,cy-1);y<=Math.min(V879_TILE_NY-1,cy+1);y++){
                        String path="data/nepal-waterways-tiles/"+x+"-"+y+".json";
                        List<RiverWay> ways=tileCache.get(path);if(ways==null){try{ways=v879ReadRiverAsset(path);}catch(Exception e){ways=new ArrayList<>();}tileCache.put(path,ways);}local.addAll(ways);
                    }
                    if(local.isEmpty())continue;
                    String sn=v881Norm(s.name);RiverWay bestName=null,bestAny=null;double dn=Double.POSITIVE_INFINITY,da=Double.POSITIVE_INFINITY;
                    for(RiverWay r:local){
                        if(r==null||r.points==null||r.points.size()<2)continue;double d=v881DistanceToRiverKm(s.lat,s.lon,r);if(!Double.isFinite(d))continue;
                        String rn=v881Norm(r.name);boolean nm=!rn.isEmpty()&&!sn.isEmpty()&&(rn.equals(sn)||rn.contains(sn)||sn.contains(rn));
                        if(nm&&d<dn){dn=d;bestName=r;}if(d<da){da=d;bestAny=r;}
                    }
                    RiverWay seed=bestName!=null?bestName:bestAny;if(seed==null)continue;chosen.add(seed);
                    String key=v881Norm(seed.name);if(!key.isEmpty())for(RiverWay r:local){String rn=v881Norm(r.name);if(!key.equals(rn))continue;double d=v881DistanceToRiverKm(s.lat,s.lon,r);if(Double.isFinite(d)&&d<=18d)chosen.add(r);}
                }
                final List<RiverWay> selected=v879Dedup(new ArrayList<>(chosen));
                final String geo=selected.isEmpty()?emptyFeatureCollection():makeRiversGeoJson(selected);
                main.post(()->{
                    v893StationRivers.clear();v893StationRivers.addAll(selected);v893StationRiverGeoJson=geo;v894StationGeometryFingerprint=fingerprint;
                    v893EnsureDedicatedLayers();v893SetGeo("fs-v893-station-rivers",geo);v894UpdateDedicatedStatus(ss);if(v896RiverOverlay!=null)v896RiverOverlay.invalidate();
                });
            }catch(Exception ignored){}finally{
                v894RiverMatchRunning=false;
                if(!v894PendingFingerprint.equals(v894StationGeometryFingerprint))main.post(this::v893RefreshDedicatedStationRivers);
            }
        });
    } // V0896_EXACT_LOCAL_TILE_STATION_RIVERS
'''
m=replace_method(m,'v893RefreshDedicatedStationRivers',refresh)

old='main.post(()->{v893EnsureDedicatedLayers();v893SetGeo("fs-v893-alert",ag);v893SetGeo("fs-v893-warning",wg);v893SetGeo("fs-v893-danger",dg);});'
if old in m:m=m.replace(old,'main.post(()->{v893EnsureDedicatedLayers();v893SetGeo("fs-v893-alert",ag);v893SetGeo("fs-v893-warning",wg);v893SetGeo("fs-v893-danger",dg);if(v896RiverOverlay!=null)v896RiverOverlay.invalidate();});',1)

overlay=r'''
    private final class V896RiverOverlay extends android.view.View {
        private final android.graphics.Paint glow=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        private final android.graphics.Paint core=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        private final android.graphics.Paint flow=new android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG);
        V896RiverOverlay(Context c){super(c);setClickable(false);setFocusable(false);glow.setStyle(android.graphics.Paint.Style.STROKE);glow.setStrokeCap(android.graphics.Paint.Cap.ROUND);glow.setStrokeJoin(android.graphics.Paint.Join.ROUND);core.setStyle(android.graphics.Paint.Style.STROKE);core.setStrokeCap(android.graphics.Paint.Cap.ROUND);core.setStrokeJoin(android.graphics.Paint.Join.ROUND);flow.setStyle(android.graphics.Paint.Style.FILL);setWillNotDraw(false);}
        @Override protected void onDraw(android.graphics.Canvas canvas){super.onDraw(canvas);if(map==null||v893StationRivers.isEmpty()){postInvalidateDelayed(250);return;}
            List<StationDot> ss; synchronized(stations){ss=new ArrayList<>(stations);}List<RiverWay> rs=new ArrayList<>(v893StationRivers);long now=System.currentTimeMillis();int particleCount=0;
            for(RiverWay r:rs){if(r==null||r.points==null||r.points.size()<2)continue;android.graphics.Path path=new android.graphics.Path();boolean started=false,visible=false;java.util.ArrayList<android.graphics.PointF> pts=new java.util.ArrayList<>();
                for(double[] q:r.points){if(q==null||q.length<2)continue;android.graphics.PointF p=map.getProjection().toScreenLocation(new LatLng(q[1],q[0]));pts.add(p);if(!started){path.moveTo(p.x,p.y);started=true;}else path.lineTo(p.x,p.y);if(p.x>-80&&p.y>-80&&p.x<getWidth()+80&&p.y<getHeight()+80)visible=true;}
                if(!started||!visible)continue;String st=v884Stage(r,ss);int c=Color.rgb(99,239,255);if("danger".equals(st))c=Color.rgb(242,47,75);else if("warning".equals(st))c=Color.rgb(255,138,31);else if("alert".equals(st))c=Color.rgb(255,201,40);
                float pulse=(float)((Math.sin((now%1800L)/1800.0*Math.PI*2.0)+1.0)/2.0);glow.setColor(c);glow.setAlpha(90+(int)(pulse*55));glow.setStrokeWidth(12f+pulse*4f);core.setColor(c);core.setAlpha(255);core.setStrokeWidth(4.8f);canvas.drawPath(path,glow);canvas.drawPath(path,core);
                if(pts.size()>1&&particleCount<72){double phase=((now/22L)+(particleCount*37))%1000/1000.0;int idx=Math.min(pts.size()-1,(int)Math.floor(phase*(pts.size()-1)));android.graphics.PointF fp=pts.get(idx);flow.setColor(Color.WHITE);flow.setAlpha(230);canvas.drawCircle(fp.x,fp.y,3.2f,flow);particleCount++;}
            }postInvalidateDelayed(80);
        }
    } // V0896_NATIVE_CANVAS_FLOW_GLOW_GUARANTEE
'''
anchor='    private StationDot readStation(Object o)'
if anchor not in m: raise SystemExit('readStation anchor missing')
m=m.replace(anchor,overlay+'\n'+anchor,1)

g=re.sub(r'versionCode\s+115\b','versionCode 116',g,count=1)
g=g.replace("versionName '0.8.95'","versionName '0.8.96'",1)
for token in ['V0896_GUARANTEED_CANVAS_RIVER_RENDER','V0896_EXACT_LOCAL_TILE_STATION_RIVERS','V0896_NATIVE_CANVAS_FLOW_GLOW_GUARANTEE','data/nepal-waterways-tiles/']:
    if token not in m: raise SystemExit('missing '+token)
if "versionName '0.8.96'" not in g or 'versionCode 116' not in g: raise SystemExit('version bump failed')
m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')
print('v0.8.96 PASS: exact station-local tiles + native canvas cyan/status flow-glow overlay')
