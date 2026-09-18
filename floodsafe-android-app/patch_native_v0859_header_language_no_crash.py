from pathlib import Path

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.59 is intentionally narrow:
# - remove the floating language button
# - keep one language switch in the top header
# - switch language in-place (NO recreate / NO Activity restart)
# - clean the outside-Nepal notice
# - do not touch river/map/20-minute/2-km/source logic

# 1) Remove the floating language button added in v0.8.57.
start='        Button langFloat=button(t("🌐 English","🌐 नेपाली"));'
marker=' // V0857_FLOATING_LANGUAGE'
if start in a:
    i=a.find(start)
    j=a.find(marker,i)
    if j<0: raise SystemExit('v0859 floating language end marker missing')
    j=a.find('\n',j)
    if j<0: j=len(a)
    else: j+=1
    a=a[:i]+a[j:]
if 'V0857_FLOATING_LANGUAGE' in a:
    raise SystemExit('v0859 floating language button still present')

# 2) Replace the crash-prone Activity restart with safe in-place language update.
old='langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();Intent r=new Intent(this,NativeFullActivity.class);r.addFlags(Intent.FLAG_ACTIVITY_NO_ANIMATION|Intent.FLAG_ACTIVITY_CLEAR_TOP);startActivity(r);finish();overridePendingTransition(0,0);}); // V0856_SAFE_LANGUAGE_RESTART'
new='langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();applyLanguage();v0859RefreshStaticText(root);refreshRiverUi();}); // V0859_INPLACE_LANGUAGE_SWITCH'
if old in a:
    a=a.replace(old,new,1)
elif 'V0859_INPLACE_LANGUAGE_SWITCH' not in a:
    raise SystemExit('v0859 language click anchor missing')

# 3) Keep the switch in the top header with a fixed compact width.
old='LinearLayout.LayoutParams langLp=new LinearLayout.LayoutParams(dp(84),dp(44));row.addView(langBtn,langLp); // V0856_LANGUAGE_VISIBLE'
new='LinearLayout.LayoutParams langLp=new LinearLayout.LayoutParams(dp(94),dp(42));langLp.setMargins(dp(6),0,0,0);row.addView(langBtn,langLp); // V0859_HEADER_LANGUAGE'
if old in a:
    a=a.replace(old,new,1)
elif 'V0859_HEADER_LANGUAGE' not in a:
    raise SystemExit('v0859 header language layout anchor missing')

# The button shows the target language: Nepali UI -> English, English UI -> नेपाली.
a=a.replace('langBtn.setText(t("अङ्ग्रेजी","नेपाली"));','langBtn.setText(t("English","नेपाली"));')

# 4) Refresh the one-time labels in place too, so switching does not require rebuilding the Activity.
helper=r'''    private void v0859RefreshStaticText(View node){
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
                else if(s.equals("🛡️ मेरो निगरानी क्षेत्रको बाढी जोखिम"))tv.setText("🛡️ Flood risk near me");
                else if(s.equals("सबै आधिकारिक मापन केन्द्र")||s.equals("सबै official स्टेशन"))tv.setText("Official stations");
                else if(s.equals("चेतावनी"))tv.setText("Warning");
                else if(s.equals("खतरा"))tv.setText("Danger");
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
                else if(s.equals("🧑‍🤝‍🧑 मानवीय अवस्था — पछिल्लो विपद्")||s.equals("🧑‍🤝‍🧑 Human Status — पछिल्लो विपद्"))tv.setText("🧑‍🤝‍🧑 Human Status — latest disaster");
            }else{
                if(s.equals("◎ My current location"))tv.setText("◎ मेरो हालको स्थान");
                else if(s.equals("⚠️ River warning"))tv.setText("⚠️ नदी चेतावनी");
                else if(s.equals("LIVE"))tv.setText("प्रत्यक्ष");
                else if(s.equals("＋ Zoom"))tv.setText("＋ ठूलो");
                else if(s.equals("− Out"))tv.setText("− सानो");
                else if(s.equals("🇳🇵 Nepal"))tv.setText("🇳🇵 नेपाल");
                else if(s.equals("🛡️ Flood risk near me"))tv.setText("🛡️ मेरो निगरानी क्षेत्रको बाढी जोखिम");
                else if(s.equals("Official stations"))tv.setText("सबै आधिकारिक मापन केन्द्र");
                else if(s.equals("Warning"))tv.setText("चेतावनी");
                else if(s.equals("Danger"))tv.setText("खतरा");
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
                else if(s.equals("🧑‍🤝‍🧑 Human Status — latest disaster"))tv.setText("🧑‍🤝‍🧑 मानवीय अवस्था — पछिल्लो विपद्");
            }
        }
        if(node instanceof ViewGroup){ViewGroup vg=(ViewGroup)node;for(int i=0;i<vg.getChildCount();i++)v0859RefreshStaticText(vg.getChildAt(i));}
    } // V0859_STATIC_LANGUAGE_REFRESH

'''
anchor='    private String t(String ne,String en){return english?en:ne;}'
if 'V0859_STATIC_LANGUAGE_REFRESH' not in a:
    if anchor not in a: raise SystemExit('v0859 t() anchor missing')
    a=a.replace(anchor,helper+anchor,1)

# Ensure every applyLanguage pass also refreshes static controls.
needle='updateOutsideNotice();}'
if 'v0859RefreshStaticText(root); // V0859_APPLY_STATIC_LANGUAGE' not in a:
    pos=a.find(needle)
    if pos<0: raise SystemExit('v0859 applyLanguage end anchor missing')
    a=a[:pos]+'updateOutsideNotice();v0859RefreshStaticText(root); // V0859_APPLY_STATIC_LANGUAGE\n    }'+a[pos+len(needle):]

# 5) Replace the large mixed outside-Nepal paragraph with a compact language-clean line.
start='    private void updateOutsideNotice(){'
end='    private void requestLocation(){'
i=a.find(start);j=a.find(end,i)
if i<0 or j<0: raise SystemExit('v0859 outside notice anchors missing')
notice=r'''    private void updateOutsideNotice(){
        TextView v=root==null?null:root.findViewById(android.R.id.hint);if(v==null)return;
        boolean out=Double.isFinite(lat)&&Double.isFinite(lon)&&!isNepal(lat,lon);
        v.setVisibility(out?View.VISIBLE:View.GONE);
        if(out)v.setText(t("🌍 नेपाल बाहिर • स्थानीय मौसम मात्र","🌍 Outside Nepal • local weather only"));
    } // V0859_COMPACT_OUTSIDE_NOTICE

'''
a=a[:i]+notice+a[j:]

# No restart/recreate may remain on language click.
if 'V0856_SAFE_LANGUAGE_RESTART' in a: raise SystemExit('v0859 old Activity restart still present')
if 'recreate();}); // V0854_LANGUAGE_REBUILD' in a: raise SystemExit('v0859 recreate language crash path still present')

# Build identity only.
if 'versionCode 78' in g:g=g.replace('versionCode 78','versionCode 79',1)
elif 'versionCode 79' not in g:raise SystemExit('v0859 versionCode anchor missing')
if "versionName '0.8.58'" in g:g=g.replace("versionName '0.8.58'","versionName '0.8.59'",1)
elif "versionName '0.8.59'" not in g:raise SystemExit('v0859 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

for needle in ['V0859_INPLACE_LANGUAGE_SWITCH','V0859_HEADER_LANGUAGE','V0859_STATIC_LANGUAGE_REFRESH','V0859_APPLY_STATIC_LANGUAGE','V0859_COMPACT_OUTSIDE_NOTICE','RIVER_FRESH_MS=20L*60L*1000L','V0858_STATION_DETAIL_LAST_READING']:
    if needle not in a:raise SystemExit('v0859 verification failed: '+needle)
for needle in ['versionCode 79',"versionName '0.8.59'"]:
    if needle not in g:raise SystemExit('v0859 version verification failed: '+needle)

# Hard guards: requested river/safety rules must stay untouched.
if 'bestD<=2d&&best.fresh&&(best.stage.equals("warning")||best.stage.equals("danger"))' not in a:
    raise SystemExit('v0859 2 km fresh-only emergency guard changed')
if 'main.postDelayed(this,10_000L);' not in a:
    raise SystemExit('v0859 official 10-second poll changed')

print('FloodSafe v0.8.59 PASS: header language switch + no restart crash + compact notice; river/safety logic unchanged')
