from pathlib import Path
import re

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

# v0.8.61 is intentionally narrow:
# - map river/station taps must show the same retained official measurement truth as the cards
# - remove STALE/UNKNOWN-only river popup when an older official value actually exists
# - complete English/Nepali switching for visible native UI without Activity restart/recreate
# - keep source availability green/black, blue Nepal GPS point, 20-minute safety freshness,
#   2 km emergency radius, weather logic, official polling, river geometry and animation unchanged

# -----------------------------------------------------------------------------
# 1) Full visible language refresh. No Activity restart/recreate.
# -----------------------------------------------------------------------------
lang=r'''    private void applyLanguage(){
        brandSub.setText(t("नेपाल • नदी • बाढी • चौबीसै घण्टा चेतावनी","Nepal • rivers • floods • 24/7 alerts"));
        langBtn.setText(t("English","नेपाली"));

        if(currentWeather==null)currentWeather="";
        String cw=currentWeather.trim();
        if(cw.equals("Rain now")||cw.equals("अहिले वर्षा भइरहेको छ")){currentWeather=t("अहिले वर्षा भइरहेको छ","Rain now");weatherText.setText(currentWeather);}
        else if(cw.equals("No rain now")||cw.equals("अहिले वर्षा छैन")){currentWeather=t("अहिले वर्षा छैन","No rain now");weatherText.setText(currentWeather);}
        else if(cw.isEmpty())weatherText.setText(t("नेपालको निगरानी स्थान छान्नुहोस्","Choose a monitoring location"));

        weatherSupport.setText(t("स्थानीय मौसम र BIPAD/DHM को आधिकारिक नदी अवस्था","Local weather and official BIPAD/DHM river status"));
        if(!Double.isFinite(lat)){
            place.setText(t("📍 नेपालमा निगरानी स्थान छान्नुहोस्","📍 Choose a monitoring location"));
            rainTiming.setText(t("हालको स्थान पाएपछि आगामी वर्षाको समय देखाइन्छ।","Rain timing appears after your current location is available."));
        }
        mapTitle.setText(t("🇳🇵 नेपालको प्रत्यक्ष नदी नक्सा","🇳🇵 Nepal live river map"));
        mapSub.setText(t("नदी वा मापन केन्द्र थिचेर पानीको तह, चेतावनी र आधिकारिक समय हेर्नुहोस्।","Tap a river or station to see water level, warnings and official time."));
        mapHint.setText(t("🇳🇵 आधिकारिक नदी मापन केन्द्र र नदीको नक्सा","🇳🇵 official river stations and river map"));
        nearTitle.setText(t("🌊 नजिकका नदी मापन केन्द्र","🌊 Nearby river stations"));
        nearSub.setText(t("तपाईंको हालको जीपीएसबाट दूरीअनुसार नजिकका आधिकारिक नदी मापन केन्द्र","Official river stations nearest to your current GPS, sorted by distance"));
        nationalTitle.setText(t("🏞️ जिल्ला अनुसार नदी अवस्था","🏞️ River status by district"));
        nationalSub.setText(t("जिल्ला छानेर आधिकारिक नदी मापन केन्द्र हेर्नुहोस्।","Choose a district to see official river stations."));
        newsTitle.setText(t("📰 नेपालका पछिल्ला समाचार","📰 Latest Nepal news"));
        privacyTitle.setText(t("🔒 गोपनीयता र सुरक्षा","🔒 Privacy and safety"));
        privacySub.setText(t("स्थान, माइक्रोफोन र चेतावनीसम्बन्धी जानकारी कसरी प्रयोग हुन्छ हेर्नुहोस्।","See how location, microphone and alert data are used."));
        if(districtPicker!=null&&selectedDistrict.isEmpty())districtPicker.setText(t("जिल्ला छान्नुहोस् ▾","Choose district ▾"));
        if(map!=null)map.setEnglish(english);
        updateOutsideNotice();
        v0861RefreshStaticText(root);
        if(Double.isFinite(lat)&&Double.isFinite(lon))fetchWeather(lat,lon);
    } // V0861_FULL_LANGUAGE_APPLY

    private void v0861RefreshStaticText(View node){
        if(node==null)return;
        if(node instanceof TextView){
            TextView tv=(TextView)node;String s=String.valueOf(tv.getText());
            if(english){
                if(s.equals("◎ मेरो हालको स्थान"))tv.setText("◎ My current location");
                else if(s.equals("⚠️ नदी चेतावनी"))tv.setText("⚠️ River warning");
                else if(s.equals("प्रत्यक्ष"))tv.setText("LIVE");
                else if(s.equals("＋ ठूलो"))tv.setText("＋ Zoom");
                else if(s.equals("− सानो"))tv.setText("− Out");
                else if(s.equals("🇳🇵 नेपाल"))tv.setText("🇳🇵 Nepal");
                else if(s.equals("वर्षा"))tv.setText("Rain");
                else if(s.equals("आर्द्रता"))tv.setText("Humidity");
                else if(s.equals("हावा"))tv.setText("Wind");
                else if(s.equals("🛡️ मेरो निगरानी क्षेत्रको बाढी जोखिम"))tv.setText("🛡️ Flood risk near me");
                else if(s.equals("सबै आधिकारिक मापन केन्द्र")||s.equals("सबै official स्टेशन"))tv.setText("Official stations");
                else if(s.equals("चेतावनी"))tv.setText("Warning");
                else if(s.equals("खतरा"))tv.setText("Danger");
                else if(s.equals("जिल्ला छान्नुहोस् ▾"))tv.setText("Choose district ▾");
                else if(s.equals("सबै स्टेशन देखाउनुहोस्"))tv.setText("Show all stations");
                else if(s.equals("कम देखाउनुहोस्"))tv.setText("Show less");
                else if(s.equals("मृतक"))tv.setText("Deaths");
                else if(s.equals("घाइते"))tv.setText("Injured");
                else if(s.equals("बेपत्ता"))tv.setText("Missing");
                else if(s.equals("उद्धार"))tv.setText("Rescued");
                else if(s.equals("गोपनीयता नीति हेर्नुहोस् →"))tv.setText("View privacy policy →");
                else if(s.equals("⌂\nगृह"))tv.setText("⌂\nHome");
                else if(s.equals("🗺️\nनदी नक्सा"))tv.setText("🗺️\nRiver map");
                else if(s.equals("🔔\nसमाचार"))tv.setText("🔔\nNews");
                else if(s.equals("🔔\nसूचना"))tv.setText("🔔\nAlerts");
                else if(s.equals("☰\nथप")||s.equals("≡\nथप"))tv.setText("☰\nMore");
                else if(s.equals("🧑‍🤝‍🧑 मानवीय अवस्था — पछिल्लो विपद्")||s.equals("🧑‍🤝‍🧑 Human Status — पछिल्लो विपद्"))tv.setText("🧑‍🤝‍🧑 Human Status — latest disaster");
            }else{
                if(s.equals("◎ My current location"))tv.setText("◎ मेरो हालको स्थान");
                else if(s.equals("⚠️ River warning"))tv.setText("⚠️ नदी चेतावनी");
                else if(s.equals("LIVE"))tv.setText("प्रत्यक्ष");
                else if(s.equals("＋ Zoom"))tv.setText("＋ ठूलो");
                else if(s.equals("− Out"))tv.setText("− सानो");
                else if(s.equals("🇳🇵 Nepal"))tv.setText("🇳🇵 नेपाल");
                else if(s.equals("Rain"))tv.setText("वर्षा");
                else if(s.equals("Humidity"))tv.setText("आर्द्रता");
                else if(s.equals("Wind"))tv.setText("हावा");
                else if(s.equals("🛡️ Flood risk near me"))tv.setText("🛡️ मेरो निगरानी क्षेत्रको बाढी जोखिम");
                else if(s.equals("Official stations"))tv.setText("सबै आधिकारिक मापन केन्द्र");
                else if(s.equals("Warning"))tv.setText("चेतावनी");
                else if(s.equals("Danger"))tv.setText("खतरा");
                else if(s.equals("Choose district ▾"))tv.setText("जिल्ला छान्नुहोस् ▾");
                else if(s.equals("Show all stations"))tv.setText("सबै स्टेशन देखाउनुहोस्");
                else if(s.equals("Show less"))tv.setText("कम देखाउनुहोस्");
                else if(s.equals("Deaths"))tv.setText("मृतक");
                else if(s.equals("Injured"))tv.setText("घाइते");
                else if(s.equals("Missing"))tv.setText("बेपत्ता");
                else if(s.equals("Rescued"))tv.setText("उद्धार");
                else if(s.equals("View privacy policy →"))tv.setText("गोपनीयता नीति हेर्नुहोस् →");
                else if(s.equals("⌂\nHome"))tv.setText("⌂\nगृह");
                else if(s.equals("🗺️\nRiver map"))tv.setText("🗺️\nनदी नक्सा");
                else if(s.equals("🔔\nNews"))tv.setText("🔔\nसमाचार");
                else if(s.equals("🔔\nAlerts"))tv.setText("🔔\nसूचना");
                else if(s.equals("☰\nMore")||s.equals("≡\nMore"))tv.setText("☰\nथप");
                else if(s.equals("🧑‍🤝‍🧑 Human Status — latest disaster"))tv.setText("🧑‍🤝‍🧑 मानवीय अवस्था — पछिल्लो विपद्");
            }
        }
        if(node instanceof ViewGroup){ViewGroup vg=(ViewGroup)node;for(int i=0;i<vg.getChildCount();i++)v0861RefreshStaticText(vg.getChildAt(i));}
    } // V0861_FULL_STATIC_LANGUAGE

'''
a=between(a,'    private void applyLanguage(){','    private String t(String ne,String en){return english?en:ne;}',lang,'v0861 language block')

# Header click remains in-place, but use only the new full apply pass.
a=a.replace('applyLanguage();v0859RefreshStaticText(root);refreshRiverUi();','applyLanguage();refreshRiverUi();')

# Clean a few mixed dynamic strings that survive old patch layers.
repls={
    't("Official नदी अवस्था refresh हुँदैछ…","Refreshing official river status…")':'t("आधिकारिक नदी अवस्था अद्यावधिक हुँदैछ…","Refreshing official river status…")',
    't("River data refresh हुन सकेन • stale लाई live भनिएको छैन","River refresh failed • stale data is not live")':'t("नदीको जानकारी अद्यावधिक हुन सकेन • पुरानो मापनलाई प्रत्यक्ष मानिएको छैन","River refresh failed • stale data is not live")',
    't("मौसम data refresh हुँदैछ।","Weather data is refreshing.")':'t("मौसमको जानकारी अद्यावधिक हुँदैछ।","Weather data is refreshing.")',
    't("मौसम refresh हुन सकेन","Weather refresh failed")':'t("मौसम अद्यावधिक हुन सकेन","Weather refresh failed")',
    't("वर्षा timing उपलब्ध छैन","Rain timing unavailable")':'t("वर्षाको समय उपलब्ध छैन","Rain timing unavailable")',
    't("जिल्ला data refresh हुँदैछ।","District data is refreshing.")':'t("जिल्लाको जानकारी अद्यावधिक हुँदैछ।","District data is refreshing.")'
}
for old,new in repls.items():
    a=a.replace(old,new)

# -----------------------------------------------------------------------------
# 2) Map popup truth: carry source fields into StationDot and never collapse an
#    available older official reading to a bare UNKNOWN popup.
# -----------------------------------------------------------------------------
# Map language state is driven by the Activity's current language.
if 'private boolean englishUi=false; // V0861_MAP_LANGUAGE' not in m:
    marker='    boolean terrain = true;'
    if marker not in m: raise SystemExit('v0861 terrain field missing')
    m=m.replace(marker,marker+'\n    private boolean englishUi=false; // V0861_MAP_LANGUAGE',1)

if 'void setEnglish(boolean value)' not in m:
    marker='    void zoomBy(float factor) {'
    if marker not in m: raise SystemExit('v0861 zoomBy anchor missing')
    m=m.replace(marker,'    void setEnglish(boolean value){englishUi=value;} // V0861_MAP_LANGUAGE_SET\n\n'+marker,1)

# StationDot already has online from v0.8.50. Extend it with retained official detail.
old='Object original; String name, stage; double lat, lon, level; boolean fresh, online;'
new='Object original; String name, stage, rawStatus; double lat, lon, level, warning, danger; long at; boolean fresh, online; // V0861_MAP_STATION_DETAIL_FIELDS'
if old in m:
    m=m.replace(old,new,1)
elif 'V0861_MAP_STATION_DETAIL_FIELDS' not in m:
    raise SystemExit('v0861 StationDot fields anchor missing')

read_anchor='            s.level = getDouble(c, o, "level");'
if 'V0861_READ_STATION_DETAIL' not in m:
    if read_anchor not in m: raise SystemExit('v0861 readStation level anchor missing')
    m=m.replace(read_anchor,read_anchor+'\n            s.warning = getDouble(c, o, "warning"); s.danger = getDouble(c, o, "danger");\n            s.at = getLong(c, o, "at", 0L); s.rawStatus = getString(c, o, "rawStatus", ""); // V0861_READ_STATION_DETAIL',1)

if 'private static long getLong(' not in m:
    anchor='    private static String getString(Class<?> c, Object o, String name, String fallback) {'
    helper='''    private static long getLong(Class<?> c,Object o,String name,long fallback){\n        try{Field f=c.getDeclaredField(name);f.setAccessible(true);Object v=f.get(o);return v instanceof Number?((Number)v).longValue():fallback;}catch(Exception e){return fallback;}\n    } // V0861_GET_LONG\n'''
    if anchor not in m: raise SystemExit('v0861 getString anchor missing')
    m=m.replace(anchor,helper+anchor,1)

river=r'''    private void showRiver(RiverWay r, double la, double lo) {
        StationDot gauge = nearestStation(la, lo);
        StringBuilder msg = new StringBuilder();
        if (gauge != null) {
            double d = km(la, lo, gauge.lat, gauge.lon);
            msg.append(gauge.online?"🟢 ":"⚫ ")
                    .append(englishUi?"Nearest official station: ":"नजिकको आधिकारिक मापन केन्द्र: ")
                    .append(gauge.name).append(String.format(Locale.US, " • %.1f km", d));
            msg.append("\n").append(englishUi?"Source availability: ":"स्रोत उपलब्धता: ")
                    .append(gauge.online?(englishUi?"available in latest official source":"पछिल्लो आधिकारिक स्रोतमा उपलब्ध"):(englishUi?"not in latest official source":"पछिल्लो आधिकारिक स्रोतमा उपलब्ध छैन"));
            if (Double.isFinite(gauge.level)) msg.append(String.format(Locale.US, englishUi?"\nLast official water level: %.2f m":"\nअन्तिम आधिकारिक पानीको सतह: %.2f m", gauge.level));
            if (gauge.at > 0L) {
                msg.append("\n").append(englishUi?"Measurement time: ":"मापन समय: ").append(v0861MapTime(gauge.at));
                msg.append("\n").append(englishUi?"Age: ":"कति अघि: ").append(v0861MapAge(gauge.at));
            }
            if(Double.isFinite(gauge.warning))msg.append(String.format(Locale.US,englishUi?"\nWarning level: %.2f m":"\nचेतावनी तह: %.2f m",gauge.warning));
            if(Double.isFinite(gauge.danger))msg.append(String.format(Locale.US,englishUi?"\nDanger level: %.2f m":"\nखतरा तह: %.2f m",gauge.danger));
            msg.append("\n").append(englishUi?"Safety status: ":"सुरक्षा अवस्था: ")
                    .append(gauge.fresh?v0861MapStage(gauge.stage):(englishUi?"older official reading — not live":"पुरानो आधिकारिक मापन — प्रत्यक्ष होइन"));
            if(!Double.isFinite(gauge.level)||gauge.at<=0L)msg.append("\n").append(englishUi?"The source does not currently provide a measurement value/time for this station.":"यस मापन केन्द्रका लागि स्रोतले हाल मापनको मान वा समय उपलब्ध गराएको छैन।");
            msg.append("\n\n").append(englishUi?"Source: official BIPAD/DHM river measurement":"स्रोत: BIPAD/DHM आधिकारिक नदी मापन");
        } else {
            msg.append(englishUi?"No direct official gauge reference was found near this river segment.":"यो नदी खण्ड नजिक प्रत्यक्ष आधिकारिक मापन केन्द्र भेटिएन।");
            msg.append("\n\n").append(englishUi?"River geometry: OpenStreetMap / FloodSafe bundled network":"नदीको नक्सा: OpenStreetMap / FloodSafe मा समावेश गरिएको नदी सञ्जाल");
        }
        new AlertDialog.Builder(getContext()).setTitle(r.name).setMessage(msg.toString()).setPositiveButton(englishUi?"OK":"ठीक छ", null).show();
    } // V0861_RIVER_DETAIL_PARITY

    private String v0861MapStage(String stage){
        String s=stage==null?"":stage.toLowerCase(Locale.ROOT);
        if(s.contains("danger"))return englishUi?"Danger":"खतरा";
        if(s.contains("warning"))return englishUi?"Warning":"चेतावनी";
        if(s.contains("alert")||s.contains("watch"))return englishUi?"Alert":"सतर्कता";
        if(s.contains("normal"))return englishUi?"Normal":"सामान्य";
        return englishUi?"Official reading":"आधिकारिक मापन";
    }
    private String v0861MapAge(long at){
        if(at<=0)return englishUi?"time unavailable":"समय उपलब्ध छैन";
        long min=Math.max(0,(System.currentTimeMillis()-at)/60000L);
        if(min<60)return englishUi?min+" min ago":min+" मिनेटअघि";
        long h=min/60;if(h<48)return englishUi?h+" h ago":h+" घण्टाअघि";
        long d=h/24;return englishUi?d+" d ago":d+" दिनअघि";
    }
    private String v0861MapTime(long at){
        try{return java.time.Instant.ofEpochMilli(at).atZone(java.time.ZoneId.of("Asia/Kathmandu")).format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss 'NPT'"));}
        catch(Exception e){return englishUi?"time unavailable":"समय उपलब्ध छैन";}
    }

'''
m=between(m,'    private void showRiver(RiverWay r, double la, double lo) {','    private void startParticles() {',river,'v0861 river detail')

# Make tapping a visible station less likely to fall through to the river popup.
m=m.replace('kmPerPixel*22.0','kmPerPixel*34.0')
if 'kmPerPixel*34.0' not in m: raise SystemExit('v0861 station tap radius update missing')

# Activity passes current language to the map immediately after creation/updates via applyLanguage.
if 'map.setEnglish(english);' not in a: raise SystemExit('v0861 map language bridge missing')

# -----------------------------------------------------------------------------
# 3) Build identity only.
# -----------------------------------------------------------------------------
if 'versionCode 80' in g:g=g.replace('versionCode 80','versionCode 81',1)
elif 'versionCode 81' not in g:raise SystemExit('v0861 versionCode anchor missing')
if "versionName '0.8.60'" in g:g=g.replace("versionName '0.8.60'","versionName '0.8.61'",1)
elif "versionName '0.8.61'" not in g:raise SystemExit('v0861 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');m_path.write_text(m,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

# Hard guards against regressions outside the user's requested scope.
for needle in ['V0861_FULL_LANGUAGE_APPLY','V0861_FULL_STATIC_LANGUAGE','V0860_SOURCE_AVAILABILITY_DOT','V0860_SOURCE_AVAILABILITY_ROW','V0860_SOURCE_PARITY_DETAIL','RIVER_FRESH_MS=20L*60L*1000L','main.postDelayed(this,10_000L);']:
    if needle not in a:raise SystemExit('v0861 activity verification failed: '+needle)
for needle in ['V0861_MAP_LANGUAGE','V0861_MAP_LANGUAGE_SET','V0861_MAP_STATION_DETAIL_FIELDS','V0861_READ_STATION_DETAIL','V0861_RIVER_DETAIL_PARITY','V0860_MAP_SOURCE_GREEN_BLACK','V0852_MAPLIBRE_USER_LOCATION','V0852_VISIBLE_GPS_DOT','circleColor("#0b7fd0")']:
    if needle not in m:raise SystemExit('v0861 map verification failed: '+needle)
if 'V0857_FLOATING_LANGUAGE' in a:raise SystemExit('v0861 floating language returned')
if 'V0856_SAFE_LANGUAGE_RESTART' in a or 'recreate();}); // V0854_LANGUAGE_REBUILD' in a:raise SystemExit('v0861 crash-prone language restart returned')
if 'bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"))' not in a:raise SystemExit('v0861 2 km fresh-only emergency guard changed')
for needle in ['versionCode 81',"versionName '0.8.61'"]:
    if needle not in g:raise SystemExit('v0861 version verification failed: '+needle)

print('FloodSafe v0.8.61 PASS: map station/river detail parity + complete visible bilingual UI; source colours/GPS/20m/2km/realtime unchanged')
