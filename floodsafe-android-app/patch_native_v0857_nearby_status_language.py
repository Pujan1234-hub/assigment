from pathlib import Path

root=Path(__file__).resolve().parent
app=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=app/'NativeFullActivity.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.57 is intentionally narrow:
# - show a persistent language switch without Activity.recreate()
# - do not show arbitrary "nearby" stations when GPS is missing/outside Nepal
# - station dots/cards represent the 20-minute safety status, not merely source availability
# Alert radius, thresholds, official sources, map geometry, weather and background logic stay unchanged.

# 1) Persistent floating language switch above SATHI.
anchor='root.addView(sathi,fp);'
if 'V0857_FLOATING_LANGUAGE' not in a:
    if anchor not in a: raise SystemExit('v0857 SATHI anchor missing')
    add='''root.addView(sathi,fp);\n        Button langFloat=button(t("🌐 English","🌐 नेपाली"));langFloat.setTextSize(12);langFloat.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();Intent r=new Intent(this,NativeFullActivity.class);r.addFlags(Intent.FLAG_ACTIVITY_NO_ANIMATION|Intent.FLAG_ACTIVITY_CLEAR_TOP);startActivity(r);finish();overridePendingTransition(0,0);});FrameLayout.LayoutParams lfp=new FrameLayout.LayoutParams(dp(112),dp(44),Gravity.END|Gravity.BOTTOM);lfp.setMargins(0,0,dp(18),dp(136));root.addView(langFloat,lfp); // V0857_FLOATING_LANGUAGE'''
    a=a.replace(anchor,add,1)

# 2) Replace refreshRiverUi so nearby list is GPS-truthful and safety colours use 20-minute freshness.
rs=a.find('    private void refreshRiverUi(){')
re=a.find('    private static String v849AvailabilityDot',rs)
if rs<0 or re<0: raise SystemExit('v0857 refreshRiverUi anchors missing')
refresh=r'''    private void refreshRiverUi(){
        if(nearList==null)return;List<RiverStation> copy;synchronized(stations){copy=new ArrayList<>(stations);}
        copy.sort(Comparator.comparingInt((RiverStation s)->s.fresh?0:1).thenComparingInt(s->s.rank).thenComparing(s->s.name,String.CASE_INSENSITIVE_ORDER));
        map.setStations(copy,lat,lon);
        int online=0,recent=0,d=0,w=0,al=0,n=0;for(RiverStation s:copy){if(s.online)online++;if(s.fresh){recent++;if("danger".equals(s.stage))d++;else if("warning".equals(s.stage))w++;else if("alert".equals(s.stage))al++;else if("normal".equals(s.stage))n++;}}
        int sourceTotal=v849CatalogCount>0?v849CatalogCount:copy.size();
        int stale=Math.max(0,sourceTotal-recent);
        stationCount.setText(String.valueOf(sourceTotal));warningCount.setText(String.valueOf(w));dangerCount.setText(String.valueOf(d));
        feedFresh.setText(t("पछिल्लो २० मिनेट: 🔴 "+d+"  🟠 "+w+"  🟡 "+al+"  🔵 "+n+" • पुरानो/अज्ञात "+stale,
                "Last 20 min: 🔴 "+d+"  🟠 "+w+"  🟡 "+al+"  🔵 "+n+" • stale/unknown "+stale)); // V0857_FRESH_STATUS_SUMMARY
        updateRisk(copy);

        nearList.removeAllViews();
        if(!Double.isFinite(lat)||!Double.isFinite(lon)){
            nearSub.setText(t("हालको जीपीएस लिएपछि वास्तविक नजिकका मापन केन्द्र देखिन्छन्।","Get current GPS to show the actual nearest river stations."));
            nearList.addView(empty(t("◎ मेरो हालको स्थान थिचेर जीपीएस स्थान लिनुहोस्।","Tap My current location to get your GPS position.")));
        }else if(!isNepal(lat,lon)){
            nearSub.setText(t("तपाईं अहिले नेपाल बाहिर हुनुहुन्छ।","You are currently outside Nepal."));
            nearList.addView(empty(t("नेपाल बाहिर हुँदा 'नजिकका नदी मापन केन्द्र' देखाइँदैन। नेपालभित्रको हालको जीपीएस भएपछि दूरीअनुसार देखिन्छ।","Nearby Nepal river stations are not shown while you are outside Nepal. They will be sorted by real distance when current GPS is inside Nepal.")));
        }else{
            nearSub.setText(t("तपाईंको हालको जीपीएसबाट दूरीअनुसार नजिकका आधिकारिक नदी मापन केन्द्र","Official river stations nearest to your current GPS, sorted by distance"));
            List<RiverStation> near=new ArrayList<>(copy);near.sort(Comparator.comparingDouble(s->distanceKm(s.lat,s.lon)));
            for(int i=0;i<Math.min(8,near.size());i++)nearList.addView(stationRow(near.get(i)));
            if(near.isEmpty())nearList.addView(empty(t("नजिकको आधिकारिक नदी मापन केन्द्र भेटिएन।","No nearby official river station was found.")));
        }

        if(nationalList!=null){nationalList.removeAllViews();if(selectedDistrict.isEmpty()){nationalFresh.setText(t("जिल्ला छानेर त्यहाँका आधिकारिक मापन केन्द्र हेर्नुहोस्।","Choose a district to view its official river stations."));nationalList.addView(empty(t("माथिबाट जिल्ला छान्नुहोस्।","Choose a district above.")));}else{int total=0,on=0,fr=0;for(RiverStation s:copy)if(selectedDistrict.equalsIgnoreCase(s.district)){total++;if(s.online)on++;if(s.fresh)fr++;nationalList.addView(stationRow(s));}nationalFresh.setText(t(selectedDistrict+": जम्मा "+total+" • पछिल्लो २० मिनेट "+fr,selectedDistrict+": total "+total+" • within 20 min "+fr));if(total==0)nationalList.addView(empty(t("आधिकारिक नदी मापन केन्द्र भेटिएन।","No official river station was found.")));}}
    } // V0857_NEARBY_GPS_TRUTH

'''
a=a[:rs]+refresh+a[re:]

# 3) Rows use safety status colours: danger red, warning orange, alert yellow, normal blue, stale/unknown grey.
ss=a.find('    private static String v849AvailabilityDot')
se=a.find('    private void updateRisk(',ss)
if ss<0 or se<0: raise SystemExit('v0857 station row anchors missing')
row=r'''    private static String v849AvailabilityDot(RiverStation s){return s!=null&&s.online?"🟢":"⚫";} // retained only for source diagnostics
    private static String v0857StatusDot(RiverStation s){if(s==null||!s.fresh)return "⚪";if("danger".equals(s.stage))return "🔴";if("warning".equals(s.stage))return "🟠";if("alert".equals(s.stage))return "🟡";if("normal".equals(s.stage))return "🔵";return "⚪";} // V0857_STATUS_DOT
    private int v0857StatusBg(RiverStation s){if(s==null||!s.fresh)return Color.rgb(244,247,249);if("normal".equals(s.stage))return Color.rgb(235,247,255);return stageBg(s.stage);} // V0857_STATUS_BG
    private View stationRow(RiverStation s){TextView v=text(v0857StatusDot(s)+"  "+s.name+"\n"+stationLine(s),14,true,Color.rgb(30,52,72));v.setPadding(dp(12),dp(10),dp(12),dp(10));v.setBackground(round(v0857StatusBg(s),17,Color.rgb(216,234,243),1));v.setOnClickListener(x->showStation(s));LinearLayout.LayoutParams p=lp(-1,-2,0,0,0,dp(7));v.setLayoutParams(p);return v;} // V0857_STATUS_ROW
'''
a=a[:ss]+row+a[se:]

# 4) Stale readings are labelled stale, not green/source-current. Add real distance when GPS is in Nepal.
ls=a.find('    private String v850Age(')
le=a.find('    private static String mapDisplayStage(',ls)
if ls<0 or le<0: raise SystemExit('v0857 stationLine anchors missing')
line=r'''    private String v850Age(long at){if(at<=0)return t("समय उपलब्ध छैन","time unavailable");long min=Math.max(0,(System.currentTimeMillis()-at)/60000L);if(min<60)return t(min+" मिनेटअघि",min+" min ago");long h=min/60;if(h<48)return t(h+" घण्टाअघि",h+" h ago");long d=h/24;return t(d+" दिनअघि",d+" d ago");}
    private String stationLine(RiverStation s){String lev=Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):t("सतह उपलब्ध छैन","level unavailable");String state;if(!s.online)state=t("हाल उपलब्ध छैन","currently unavailable");else if(!s.fresh)state=t("पुरानो मापन","STALE");else state=stageName(s.stage);double km=distanceKm(s.lat,s.lon);String dist=Double.isFinite(km)?String.format(Locale.US," • %.1f km",km):"";return state+" • "+lev+" • "+v850Age(s.at)+dist;} // V0857_STATION_LINE

'''
a=a[:ls]+line+a[le:]

# Stale/unknown map stations must also be grey rather than "latest/online" colour.
a=a.replace('if(s==null||!s.online)return "offline";\n        if(!s.fresh)return "latest";','if(s==null||!s.fresh)return "stale";',1)

# Station detail first line follows safety status too.
a=a.replace('b.append(v849AvailabilityDot(s)).append(" ").append(s.online?t("स्रोतमा उपलब्ध","Available in source"):t("अफलाइन","Offline"));','b.append(v0857StatusDot(s)).append(" ").append(s.fresh?stageName(s.stage):t("पुरानो/अज्ञात मापन","Stale/unknown observation"));',1)

# Build identity only.
if 'versionCode 76' in g:g=g.replace('versionCode 76','versionCode 77',1)
elif 'versionCode 77' not in g:raise SystemExit('v0857 versionCode anchor missing')
if "versionName '0.8.56'" in g:g=g.replace("versionName '0.8.56'","versionName '0.8.57'",1)
elif "versionName '0.8.57'" not in g:raise SystemExit('v0857 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

# Narrow verification: do not allow accidental regression of prior safety/runtime rules.
for needle in ['V0857_FLOATING_LANGUAGE','V0857_NEARBY_GPS_TRUTH','V0857_STATUS_DOT','V0857_STATUS_ROW','V0857_STATION_LINE','RIVER_FRESH_MS=20L*60L*1000L','V0856_SAFE_LANGUAGE_RESTART']:
    if needle not in a:raise SystemExit('v0857 verification failed: '+needle)
if 'recreate();}); // V0854_LANGUAGE_REBUILD' in a:raise SystemExit('unsafe recreate returned')
for needle in ['versionCode 77',"versionName '0.8.57'"]:
    if needle not in g:raise SystemExit('v0857 version verification failed: '+needle)
print('FloodSafe v0.8.57 PASS: GPS-truthful nearby list + 20-minute safety colours + persistent language switch')
