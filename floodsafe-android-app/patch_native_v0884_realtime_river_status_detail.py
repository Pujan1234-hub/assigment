from pathlib import Path
import re

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.84 real-device correction.
# The v0.8.83 field video proved that marker-only verification was not enough:
# river popup omitted time/source/thresholds and severe station colour did not visibly
# propagate to the matching river geometry. This final override runs after v0.8.83.
# Safety invariants remain: only fresh official readings colour rivers, named rivers use
# exact canonical same-river matching, no nearby different-river gauge is borrowed.

def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*(?:throws\s+[^{]+)?\{',text)
    if not q:return None
    op=text.find('{',q.start());depth=0;quote=None;esc=False;i=op
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
                if depth==0:return q.start(),i+1
        i+=1
    return None

def replace_method(text,name,new_block):
    sp=method_span(text,name)
    if not sp:raise SystemExit('v0884 method missing: '+name)
    return text[:sp[0]]+new_block+text[sp[1]:]

# 1) One strict canonical river key for BOTH popup matching and risk-colour propagation.
# Handles official joined names such as MaiKhola vs OSM "Mai Khola" without fuzzy matching.
if 'V0884_STRICT_CANONICAL_RIVER_KEY' not in m:
    sp=method_span(m,'v872RiskGaugeForRiver')
    if not sp:raise SystemExit('v0884 risk gauge matcher missing')
    helper=r'''    private static String v884CanonicalRiverName(String value){
        if(value==null)return "";
        String x=value.toLowerCase(Locale.ROOT).trim();
        x=x.replace("koshi","kosi").replace("nakhhu","nakhu").replace("nakkhu","nakhu").replace("sunkoshi","sunkosi");
        x=x.replaceAll("(?iu)(river|khola|nadi|stream|नदी|खोला)$"," ");
        x=x.replaceAll("[^\\p{L}\\p{N}]+"," ").trim();
        x=x.replaceAll("(?iu)\\b(river|khola|nadi|stream|नदी|खोला)\\b"," ");
        x=x.replaceAll("\\s+","").trim();
        return x;
    } // V0884_STRICT_CANONICAL_RIVER_KEY

'''
    m=m[:sp[0]]+helper+m[sp[0]:]

risk_match=r'''    private StationDot v872RiskGaugeForRiver(RiverWay r,List<StationDot> ss,String group){
        if(r==null||ss==null||!v863UsefulRiverName(r.name))return null;
        String rk=v884CanonicalRiverName(r.name);if(rk.isEmpty())return null;
        StationDot best=null;double bestD=Double.POSITIVE_INFINITY;
        for(StationDot x:ss){
            if(x==null||!x.fresh||!group.equals(normalizeStage(x.stage)))continue;
            String sk=v884CanonicalRiverName(x.riverName); // V0884_RISK_USES_OFFICIAL_RIVER_NAME
            if(sk.isEmpty()||!rk.equals(sk))continue; // exact same-river key only
            double d=v872GaugeToRiverKm(x,r);
            if(Double.isFinite(d)&&d<bestD){bestD=d;best=x;}
        }
        return bestD<=7.5?best:null; // V0872_MATCHED_RIVER_GEOMETRY_ONLY V0884_FRESH_SAME_RIVER_RISK_ONLY
    }
'''
m=replace_method(m,'v872RiskGaugeForRiver',risk_match)

# 2) Risk lines get a wide pulsing colour halo as well as a solid core.
risk_layer=r'''    private void ensureRiskLineSource(String sourceId,String layerId,String color,float width){
        if(style.getSource(sourceId)==null)style.addSource(new GeoJsonSource(sourceId,emptyFeatureCollection()));
        String glowId=layerId+"-glow";
        if(style.getLayer(glowId)==null)style.addLayer(new LineLayer(glowId,sourceId).withProperties(
                lineColor(color),lineWidth(width+5.0f),lineOpacity(0.28f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
        if(style.getLayer(layerId)==null)style.addLayer(new LineLayer(layerId,sourceId).withProperties(
                lineColor(color),lineWidth(width),lineOpacity(1.0f),lineCap(LINE_CAP_ROUND),lineJoin(LINE_JOIN_ROUND)));
    } // V0884_RISK_GLOW_LAYERS
'''
m=replace_method(m,'ensureRiskLineSource',risk_layer)

pulse=r'''    private void v847UpdateMovingGlow(long now){
        if(!styleReady||style==null||v875TouchActive)return;
        try{
            double wave=0.5+0.5*Math.sin(now/420.0);
            LineLayer baseGlow=style.getLayerAs("fs-river-glow");
            if(baseGlow!=null)baseGlow.setProperties(lineOpacity((float)(0.42+0.16*wave)),lineWidth((float)(4.4+0.8*wave)));
            LineLayer baseCore=style.getLayerAs("fs-rivers-layer");
            if(baseCore!=null)baseCore.setProperties(lineOpacity((float)(0.93+0.05*wave)),lineWidth((float)(1.75+0.22*wave)));
            String[] coreIds={"fs-river-alert-risk-layer","fs-river-warning-risk-layer","fs-river-danger-risk-layer"};
            float[] widths={4.2f,5.0f,5.8f};
            for(int i=0;i<coreIds.length;i++){
                LineLayer core=style.getLayerAs(coreIds[i]);
                if(core!=null)core.setProperties(lineOpacity(1.0f),lineWidth(widths[i]+(float)(0.55*wave)));
                LineLayer glow=style.getLayerAs(coreIds[i]+"-glow");
                if(glow!=null)glow.setProperties(lineOpacity((float)(0.22+0.28*wave)),lineWidth(widths[i]+4.5f+(float)(2.2*wave)));
            }
            LineLayer oldHalo=style.getLayerAs("fs-river-flow-anim-halo");if(oldHalo!=null)oldHalo.setProperties(lineOpacity(0.0f));
            LineLayer oldCore=style.getLayerAs("fs-river-flow-anim-core");if(oldCore!=null)oldCore.setProperties(lineOpacity(0.0f));
        }catch(Exception ignored){}
    } // V0875_LIGHTWEIGHT_FLOW_ANIMATION V0884_STATUS_COLOUR_FLOW_GLOW
'''
m=replace_method(m,'v847UpdateMovingGlow',pulse)

# 3) Rebuild status-coloured geometry after every viewport river-tile swap, not just after
# a station refresh. This fixes blue-only rivers after pan/zoom while the station dot is severe.
river_swap=r'''    private void v879ApplyRiverGeometry(List<RiverWay> input,String key,int generation){
        final List<RiverWay> next=v879Dedup(input);
        main.post(()->{
            if(generation!=v879RiverLoadGeneration||next.isEmpty())return;
            try{
                rivers.clear();rivers.addAll(next);riversGeoJson=makeRiversGeoJson(next);v879RiverGeometryKey=key;
                if(styleReady&&style!=null){GeoJsonSource s=style.getSourceAs("fs-rivers");if(s!=null)s.setGeoJson(riversGeoJson);else installGeoLayers();}
                else installGeoLayers();
                refreshRiverRiskSources(); // V0884_RISK_REFRESH_AFTER_TILE_SWAP
            }catch(Exception ignored){}
        });
    }
'''
m=replace_method(m,'v879ApplyRiverGeometry',river_swap)

# 4) Real river-first detail. Always prints timestamp/source/threshold rows, even if the
# official row omitted a value, so the user can see exactly what is and is not available.
if 'V0884_RIVER_DETAIL_HELPERS' not in m:
    sp=method_span(m,'showRiver')
    if not sp:raise SystemExit('v0884 showRiver missing')
    helpers=r'''    private StationDot v884SameRiverGaugeForDetail(RiverWay r,double la,double lo){
        if(r==null||!v863UsefulRiverName(r.name))return null;
        String rk=v884CanonicalRiverName(r.name);if(rk.isEmpty())return null;
        StationDot bestObserved=null,bestAny=null;double obsScore=Double.POSITIVE_INFINITY,anyScore=Double.POSITIVE_INFINITY;
        synchronized(stations){for(StationDot s:stations){
            if(s==null)continue;String sk=v884CanonicalRiverName(s.riverName);if(sk.isEmpty()||!rk.equals(sk))continue;
            double routeD=v872GaugeToRiverKm(s,r);if(!Double.isFinite(routeD)||routeD>7.5)continue;
            double tapD=km(la,lo,s.lat,s.lon);if(!Double.isFinite(tapD)||tapD>50.0)continue;
            double score=routeD*8.0+tapD;
            if(score<anyScore){anyScore=score;bestAny=s;}
            if((Double.isFinite(s.level)||s.v881At>0L)&&score<obsScore){obsScore=score;bestObserved=s;}
        }}
        return bestObserved!=null?bestObserved:bestAny;
    }
    private static String v884ObservationTime(StationDot s){
        if(s==null)return "";if(s.v881At>0L)return v881Time(s.v881At);
        return v881JsonString(s.v881Raw,"observationTime","observation_time","observedAt","observed_at","dataTime","data_time","timestamp","dateTime","datetime","measuredAt","measured_at","modifiedOn","modified_on","updatedAt","updated_at");
    }
    private static String v884OfficialSource(StationDot s){
        if(s==null)return "";if(s.v881Source!=null&&!s.v881Source.trim().isEmpty())return s.v881Source.trim();
        return v881JsonString(s.v881Raw,"_floodsafeSource","source","dataSource","data_source","provider","agency");
    }
    private static String v884Age(long at){
        if(at<=0L)return "";long ms=Math.max(0L,System.currentTimeMillis()-at),min=ms/60000L;
        if(min<60L)return min+" min";long h=min/60L;if(h<48L)return h+" h "+(min%60L)+" min";return (h/24L)+" d "+(h%24L)+" h";
    }
    private static String v884MapColour(StationDot s){
        if(s==null||!s.fresh)return "BLUE / no verified current risk colour";
        String st=normalizeStage(s.stage);if("danger".equals(st))return "RED";if("warning".equals(st))return "ORANGE";if("alert".equals(st))return "YELLOW";return "BLUE";
    } // V0884_RIVER_DETAIL_HELPERS

'''
    m=m[:sp[0]]+helpers+m[sp[0]:]

show=r'''    private void showRiver(RiverWay r,double la,double lo){
        StationDot gauge=v884SameRiverGaugeForDetail(r,la,lo);
        boolean named=v863UsefulRiverName(r==null?null:r.name);
        String riverName=named?r.name:(englishUi?"Mapped river / stream":"नक्सामा रहेको नदी / खोला");
        StringBuilder b=new StringBuilder();
        b.append(englishUi?"River / stream: ":"नदी / खोला: ").append(riverName);
        b.append("\n").append(englishUi?"Waterway type: ":"जलमार्ग प्रकार: ").append(r==null||r.type==null||r.type.trim().isEmpty()?"stream":r.type);
        b.append(String.format(Locale.US,"\n%s%.5f, %.5f",englishUi?"Tapped at: ":"थिचेको स्थान: ",la,lo));
        if(gauge!=null){
            String status=normalizeStage(gauge.stage).toUpperCase(Locale.ROOT);
            String obs=v884ObservationTime(gauge),src=v884OfficialSource(gauge),age=v884Age(gauge.v881At);
            b.append("\n\n").append(englishUi?"VERIFIED SAME-RIVER OFFICIAL GAUGE":"VERIFIED SAME-RIVER आधिकारिक GAUGE");
            b.append("\n").append(englishUi?"Station: ":"Station: ").append(gauge.name);
            if(gauge.riverName!=null&&!gauge.riverName.trim().isEmpty())b.append("\n").append(englishUi?"Official river name: ":"आधिकारिक नदी नाम: ").append(gauge.riverName);
            b.append(String.format(Locale.US,"\n%s%.2f km",englishUi?"Gauge distance from tap: ":"Gauge दूरी: ",km(la,lo,gauge.lat,gauge.lon)));
            b.append("\n").append(englishUi?"Status: ":"स्थिति: ").append(status).append(gauge.fresh?" • LIVE":" • NOT LIVE / LATEST OFFICIAL");
            b.append("\n").append(englishUi?"River map colour: ":"नदी नक्सा रङ: ").append(v884MapColour(gauge));
            b.append("\n").append(englishUi?"Water level: ":"पानीको सतह: ").append(Double.isFinite(gauge.level)?String.format(Locale.US,"%.3f m",gauge.level):(englishUi?"not supplied":"उपलब्ध छैन"));
            b.append("\n").append(englishUi?"Warning level: ":"Warning level: ").append(Double.isFinite(gauge.v881Warning)?String.format(Locale.US,"%.3f m",gauge.v881Warning):(englishUi?"not published for this gauge":"यो gauge का लागि प्रकाशित छैन"));
            b.append("\n").append(englishUi?"Danger level: ":"Danger level: ").append(Double.isFinite(gauge.v881Danger)?String.format(Locale.US,"%.3f m",gauge.v881Danger):(englishUi?"not published for this gauge":"यो gauge का लागि प्रकाशित छैन"));
            b.append("\n").append(englishUi?"Observation time: ":"मापन समय: ").append(obs.isEmpty()?(englishUi?"not supplied in current official row":"हालको आधिकारिक row मा उपलब्ध छैन"):obs);
            if(!age.isEmpty())b.append("\n").append(englishUi?"Reading age: ":"Reading उमेर: ").append(age);
            b.append("\n").append(englishUi?"Official source: ":"आधिकारिक स्रोत: ").append(src.isEmpty()?(englishUi?"source field not supplied":"source field उपलब्ध छैन"):src);
            if(!gauge.fresh)b.append("\n\n").append(englishUi?"This latest official reading is not treated as LIVE and does not colour the river as an active warning.":"यो पछिल्लो आधिकारिक reading लाई LIVE मानिँदैन र active warning को रङ नदीमा लगाइँदैन।");
        }else{
            b.append("\n\n").append(englishUi?"No verified official gauge can currently be mapped to this exact river segment.":"यो नदीको यही खण्डसँग मिल्ने verified आधिकारिक gauge अहिले भेटिएन।");
            b.append("\n").append(englishUi?"FloodSafe will not borrow a nearby different-river station or invent a live status.":"FloodSafe ले नजिकको अर्को नदीको station जोड्दैन र live status बनाउँदैन।");
        }
        b.append("\n\n").append(englishUi?"Status colours: Normal blue • Alert yellow • Warning orange • Danger red":"स्थिति रङ: Normal blue • Alert yellow • Warning orange • Danger red");
        b.append("\n").append(englishUi?"River geometry source: OpenStreetMap / FloodSafe Nepal network":"नदी नक्सा स्रोत: OpenStreetMap / FloodSafe Nepal नदी सञ्जाल");
        new AlertDialog.Builder(getContext()).setTitle(riverName).setMessage(b.toString()).setPositiveButton(englishUi?"OK":"ठीक छ",null).show();
    } // V0884_REAL_RIVER_DETAIL_TIME_SOURCE_THRESHOLDS V0884_NO_STATION_REDIRECT
'''
m=replace_method(m,'showRiver',show)

# Release identity after v0.8.83.
g=re.sub(r'versionCode\s+103\b','versionCode 104',g,count=1)
g=g.replace("versionName '0.8.83'","versionName '0.8.84'",1)

need=[
    'V0884_STRICT_CANONICAL_RIVER_KEY','V0884_RISK_USES_OFFICIAL_RIVER_NAME','V0884_FRESH_SAME_RIVER_RISK_ONLY',
    'V0884_RISK_GLOW_LAYERS','V0884_STATUS_COLOUR_FLOW_GLOW','V0884_RISK_REFRESH_AFTER_TILE_SWAP',
    'V0884_RIVER_DETAIL_HELPERS','V0884_REAL_RIVER_DETAIL_TIME_SOURCE_THRESHOLDS','V0884_NO_STATION_REDIRECT',
    'V0883_NEPAL_MIN_ZOOM','V0881_HYDRO_WATERBODY_GEO','V0877_CLEAN_FRESH_ONLY_LIVE'
]
for x in need:
    if x not in m:raise SystemExit('v0884 map contract missing: '+x)
if 'stationTapListener.onStationTap(gauge.original)' in m[m.find('private void showRiver'):m.find('private void showRiver')+7000]:
    raise SystemExit('v0884 river detail regressed to station redirect')
if 'x.name==null' in m[m.find('private StationDot v872RiskGaugeForRiver'):m.find('private StationDot v872RiskGaugeForRiver')+2500]:
    raise SystemExit('v0884 risk matcher still uses station display name')
if 'versionCode 104' not in g or "versionName '0.8.84'" not in g:raise SystemExit('v0884 version bump failed')

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.84 PASS: actual river popup time/source/thresholds + strict same-river fresh risk colours + pulsing status glow')
