from pathlib import Path

root=Path(__file__).resolve().parent
app=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=app/'NativeFullActivity.java'
m_path=app/'FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

def between(text,start,end,replacement,label):
    i=text.find(start)
    if i<0: raise SystemExit(label+' start missing')
    j=text.find(end,i)
    if j<0: raise SystemExit(label+' end missing')
    return text[:i]+replacement+text[j:]

# v0.8.60 is intentionally narrow:
# - make the English/Nepali switch visibly live inside the top header
# - no Activity recreate/restart on language changes
# - restore SOURCE availability station colours: green=in latest official source, black=not in latest source
# - keep 20-minute freshness only for safety decisions, not for source-availability colour
# - keep last official reading/time/age visible in station details
# - preserve the existing blue GPS point for Nepal coordinates
# - do not touch river geometry, weather, 2 km alert radius, official polling or river animation

# -----------------------------------------------------------------------------
# 1) Header: reserve real space for the language switch so it cannot disappear.
# -----------------------------------------------------------------------------
header=r'''    private View header(){
        LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);row.setGravity(Gravity.CENTER_VERTICAL);row.setPadding(0,0,0,dp(12));row.setClipChildren(false);row.setClipToPadding(false);
        ImageView icon=new ImageView(this);icon.setImageResource(R.mipmap.ic_launcher);GradientDrawable ib=round(Color.WHITE,16,Color.rgb(209,229,239),1);icon.setBackground(ib);icon.setPadding(dp(3),dp(3),dp(3),dp(3));row.addView(icon,new LinearLayout.LayoutParams(dp(48),dp(48)));
        LinearLayout brand=new LinearLayout(this);brand.setOrientation(LinearLayout.VERTICAL);brand.setPadding(dp(9),0,dp(4),0);LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(0,-2,1f);row.addView(brand,bp);
        TextView title=text("FloodSafe Nepal",22,true,Color.rgb(16,39,70));title.setSingleLine(true);brand.addView(title);brandSub=text("",11,true,Color.rgb(82,116,139));brandSub.setSingleLine(true);brand.addView(brandSub);
        langBtn=text(t("English","नेपाली"),11,true,Color.rgb(18,48,76));langBtn.setGravity(Gravity.CENTER);langBtn.setSingleLine(true);langBtn.setPadding(dp(5),0,dp(5),0);langBtn.setBackground(round(Color.WHITE,99,Color.rgb(171,207,226),1));
        langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();applyLanguage();v0859RefreshStaticText(root);refreshRiverUi();}); // V0860_LANGUAGE_INPLACE
        LinearLayout.LayoutParams langLp=new LinearLayout.LayoutParams(dp(78),dp(40));langLp.setMargins(dp(4),0,0,0);row.addView(langBtn,langLp);langBtn.bringToFront(); // V0860_HEADER_LANGUAGE_VISIBLE
        return row;
    }

'''
a=between(a,'    private View header(){','    private View hero(){',header,'v0860 header')

# -----------------------------------------------------------------------------
# 2) Station cards/list dots represent source availability again.
#    Safety/risk is still stated separately by stationLine/updateRisk.
# -----------------------------------------------------------------------------
rows=r'''    private static String v849AvailabilityDot(RiverStation s){return s!=null&&s.online?"🟢":"⚫";} // V0860_SOURCE_AVAILABILITY_DOT
    private static String v0857StatusDot(RiverStation s){if(s==null||!s.fresh)return "⚪";if("danger".equals(s.stage))return "🔴";if("warning".equals(s.stage))return "🟠";if("alert".equals(s.stage))return "🟡";if("normal".equals(s.stage))return "🔵";return "⚪";}
    private int v0857StatusBg(RiverStation s){if(s==null||!s.online)return Color.rgb(245,246,247);return Color.rgb(239,252,244);}
    private View stationRow(RiverStation s){TextView v=text(v849AvailabilityDot(s)+"  "+s.name+"\n"+stationLine(s),14,true,Color.rgb(30,52,72));v.setPadding(dp(12),dp(10),dp(12),dp(10));v.setBackground(round(v0857StatusBg(s),17,Color.rgb(216,234,243),1));v.setOnClickListener(x->showStation(s));LinearLayout.LayoutParams p=lp(-1,-2,0,0,0,dp(7));v.setLayoutParams(p);return v;} // V0860_SOURCE_AVAILABILITY_ROW
'''
a=between(a,'    private static String v849AvailabilityDot','    private void updateRisk(',rows,'v0860 station row')

# -----------------------------------------------------------------------------
# 3) Detail: source availability first, then exact retained official measurement.
#    Older values remain visible but are explicitly excluded from live safety alerts.
# -----------------------------------------------------------------------------
detail=r'''    private void showStation(RiverStation s){
        if(s==null)return;
        boolean hasReading=Double.isFinite(s.level)&&s.at>0;
        StringBuilder b=new StringBuilder();
        b.append(v849AvailabilityDot(s)).append(" ").append(s.online?t("आधिकारिक पछिल्लो स्रोतमा उपलब्ध","Available in latest official source"):t("आधिकारिक पछिल्लो स्रोतमा छैन","Not in latest official source"));
        b.append("\n").append(t("सुरक्षा अवस्था: ","Safety status: ")).append(s.fresh?stageName(s.stage):t("पुरानो मापन — प्रत्यक्ष होइन","stale reading — not live"));
        if(s.rawStatus!=null&&!s.rawStatus.trim().isEmpty()&&!s.rawStatus.contains("NOT IN LATEST SOURCE"))b.append("\n").append(t("स्रोतले दिएको अवस्था: ","Official source status: ")).append(s.rawStatus);
        if(hasReading){
            b.append("\n\n").append(t("अन्तिम आधिकारिक पानीको सतह: ","Last official water level: ")).append(String.format(Locale.US,"%.2f m",s.level));
            b.append("\n").append(t("मापन समय: ","Measurement time: ")).append(v848Time(s.at));
            b.append("\n").append(t("कति अघि: ","Age: ")).append(v850Age(s.at));
            if(Double.isFinite(s.warning))b.append("\n").append(t("चेतावनी तह: ","Warning level: ")).append(String.format(Locale.US,"%.2f m",s.warning));
            if(Double.isFinite(s.danger))b.append("\n").append(t("खतरा तह: ","Danger level: ")).append(String.format(Locale.US,"%.2f m",s.danger));
            if(!s.fresh)b.append("\n\n").append(t("यो आधिकारिक पुरानो मापन जानकारीका लागि देखाइएको हो। २० मिनेटभन्दा पुरानो मापन प्रत्यक्ष जोखिम/आपतकालीन चेतावनीमा प्रयोग हुँदैन।","This older official measurement is shown for information. Readings older than 20 minutes are not used for live risk or emergency alerts."));
        }else{
            b.append("\n\n").append(t("यस मापन केन्द्रका लागि स्रोतले पानीको सतह र मापन समय उपलब्ध गराएको छैन।","The source does not currently provide a water-level value and measurement time for this station."));
        }
        b.append("\n\n").append(t("स्रोत: BIPAD/DHM आधिकारिक नदी मापन","Source: official BIPAD/DHM river measurement"));
        new AlertDialog.Builder(this).setTitle(s.name).setMessage(b.toString()).setPositiveButton(t("ठीक छ","OK"),null).show();
    } // V0860_SOURCE_PARITY_DETAIL

'''
a=between(a,'    private void showStation(RiverStation s){','    private void refreshHuman()',detail,'v0860 station detail')

# -----------------------------------------------------------------------------
# 4) Map station-dot colours: restore green/black source parity only.
#    River risk colours/river geometry are separate and are not changed here.
# -----------------------------------------------------------------------------
colours=r'''    private void v849AvailabilityDotColours(){
        if(!styleReady||style==null)return;
        try{CircleLayer x=style.getLayerAs("fs-stale-layer");if(x!=null)x.setProperties(circleColor("#111111"),circleOpacity(1.0f),circleRadius(5.2f));}catch(Exception ignored){}
        String[] ids={"fs-normal-layer","fs-alert-layer","fs-warning-layer","fs-danger-layer"};
        for(String id:ids)try{CircleLayer x=style.getLayerAs(id);if(x!=null)x.setProperties(circleColor("#16A34A"),circleOpacity(1.0f),circleRadius(5.3f));}catch(Exception ignored){}
    } // V0860_MAP_SOURCE_GREEN_BLACK

'''
m=between(m,'    private void v849AvailabilityDotColours(){','    private void refreshUserSource()',colours,'v0860 map source colours')

# GPS point must remain the existing blue user source/layer. Do not create a fake point outside Nepal.
for marker in ['V0852_MAPLIBRE_USER_LOCATION','V0852_VISIBLE_GPS_DOT']:
    if marker not in m: raise SystemExit('v0860 GPS marker missing: '+marker)
if 'circleColor("#0b7fd0")' not in m: raise SystemExit('v0860 blue GPS layer missing')

# -----------------------------------------------------------------------------
# 5) Build identity only.
# -----------------------------------------------------------------------------
if 'versionCode 79' in g:g=g.replace('versionCode 79','versionCode 80',1)
elif 'versionCode 80' not in g:raise SystemExit('v0860 versionCode anchor missing')
if "versionName '0.8.59'" in g:g=g.replace("versionName '0.8.59'","versionName '0.8.60'",1)
elif "versionName '0.8.60'" not in g:raise SystemExit('v0860 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

# Hard guards: all previously agreed safety/runtime behaviour must survive.
for needle in ['V0860_LANGUAGE_INPLACE','V0860_HEADER_LANGUAGE_VISIBLE','V0860_SOURCE_AVAILABILITY_DOT','V0860_SOURCE_AVAILABILITY_ROW','V0860_SOURCE_PARITY_DETAIL','RIVER_FRESH_MS=20L*60L*1000L','main.postDelayed(this,10_000L);']:
    if needle not in a:raise SystemExit('v0860 activity verification failed: '+needle)
for needle in ['V0860_MAP_SOURCE_GREEN_BLACK','V0852_MAPLIBRE_USER_LOCATION','V0852_VISIBLE_GPS_DOT','circleColor("#0b7fd0")']:
    if needle not in m:raise SystemExit('v0860 map verification failed: '+needle)
if 'V0857_FLOATING_LANGUAGE' in a:raise SystemExit('v0860 floating language returned')
if 'V0856_SAFE_LANGUAGE_RESTART' in a or 'recreate();}); // V0854_LANGUAGE_REBUILD' in a:raise SystemExit('v0860 crash-prone language restart returned')
if 'bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"))' not in a:raise SystemExit('v0860 2 km fresh-only emergency guard changed')
for needle in ['versionCode 80',"versionName '0.8.60'"]:
    if needle not in g:raise SystemExit('v0860 version verification failed: '+needle)

print('FloodSafe v0.8.60 PASS: visible header language + green/black source parity + retained official detail + GPS preserved; 20m/2km/realtime unchanged')
