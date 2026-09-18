from pathlib import Path

root = Path(__file__).resolve().parent
app = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
web = root.parent / 'floodsafe-nepal' / 'v25'
a_path = app / 'NativeFullActivity.java'
w_path = app / 'RiverAlertWorker.java'
f_path = app / 'FloodSafeMessagingService.java'
g_path = root / 'app/build.gradle'
t_path = web / 'trusted-river-runtime-v3.js'
d_path = web / 'latest-official-display-policy-v1.js'
s_path = web / 'official-stale-safety-v1.js'

a = a_path.read_text(encoding='utf-8')
w = w_path.read_text(encoding='utf-8')
f = f_path.read_text(encoding='utf-8')
g = g_path.read_text(encoding='utf-8')
t = t_path.read_text(encoding='utf-8')
d = d_path.read_text(encoding='utf-8')
s = s_path.read_text(encoding='utf-8')

def once(text, old, new, label):
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise SystemExit(label + ' anchor missing')

# Build from the known-good v0.8.54 state. Do NOT apply the v0.8.55 UI patch.
# Only the requested 20-minute freshness + clean language visibility + crash-safe switch.
a = once(a, 'RIVER_FRESH_MS=5L*60L*1000L', 'RIVER_FRESH_MS=20L*60L*1000L', 'native 20m freshness')
a = once(a,
    'boolean fresh=hasObservation&&now-at<=5L*60L*1000L&&at-now<=5L*60L*1000L; // V0854_NATIVE_FIVE_MINUTE_FRESH',
    'boolean fresh=hasObservation&&now-at<=20L*60L*1000L&&at-now<=5L*60L*1000L; // V0856_NATIVE_TWENTY_MINUTE_FRESH',
    'native parsed observation 20m freshness')
w = once(w, 'MAX_AGE_MS = 5L * 60L * 1000L', 'MAX_AGE_MS = 20L * 60L * 1000L', 'worker 20m freshness')
f = once(f, 'MAX_RIVER_AGE_MS = 5L * 60L * 1000L', 'MAX_RIVER_AGE_MS = 20L * 60L * 1000L', 'fcm 20m freshness')
t = once(t, 'const FRESH_MS=5*60*1000,', 'const FRESH_MS=20*60*1000,', 'trusted 20m freshness')
t = t.replace('if(a>4*60*1000)return POLL_NEAR_STALE', 'if(a>16*60*1000)return POLL_NEAR_STALE', 1)
d = d.replace('MAX_AGE=5*60*1000', 'MAX_AGE=20*60*1000')
d = d.replace("observationPolicy:'official reading <= 5 minutes'", "observationPolicy:'official reading <= 20 minutes'")
d = d.replace('freshWindowMinutes:5', 'freshWindowMinutes:20')
d = d.replace("displayMode:'fresh-official-5m'", "displayMode:'fresh-official-20m'")
s = s.replace('const CURRENT_MS=5*60*1000,', 'const CURRENT_MS=20*60*1000,', 1)
s = s.replace('windowMinutes:5', 'windowMinutes:20', 1)

# Crash-safe language switch: avoid Activity.recreate() because the native map/background
# callbacks can still be active while recreation happens. Restart the native Activity cleanly.
a = once(a,
    'langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();recreate();}); // V0854_LANGUAGE_REBUILD',
    'langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();Intent r=new Intent(this,NativeFullActivity.class);r.addFlags(Intent.FLAG_ACTIVITY_NO_ANIMATION|Intent.FLAG_ACTIVITY_CLEAR_TOP);startActivity(r);finish();overridePendingTransition(0,0);}); // V0856_SAFE_LANGUAGE_RESTART',
    'safe language restart')

# Force the existing header switch to reserve width so it stays visible on narrow phones.
a = once(a,
    'row.addView(langBtn);',
    'LinearLayout.LayoutParams langLp=new LinearLayout.LayoutParams(dp(84),dp(44));row.addView(langBtn,langLp); // V0856_LANGUAGE_VISIBLE',
    'header language visibility')
a = a.replace('langBtn.setText(t("अङ्ग्रेजी","नेपाली"));', 'langBtn.setText(t("English","नेपाली"));')

# Clean the mixed Nepali wording without replacing view/method structure.
repl = {
    'नेपालको मौसम + official BIPAD/DHM realtime नदी status': 'स्थानीय मौसम र BIPAD/DHM को आधिकारिक नदी अवस्था',
    'नदी/स्टेशन थिचेर पानीको तह, चेतावनी र official time हेर्नुहोस्।': 'स्टेशन थिचेर पानीको तह, चेतावनी र आधिकारिक समय हेर्नुहोस्।',
    '🇳🇵 official नदी स्टेशन र नदी geometry': '🇳🇵 आधिकारिक स्टेशन र नदीको रेखा',
    'तपाईंको स्थान नजिकको official नदी अवस्था': 'तपाईंको स्थान नजिकका आधिकारिक नदी मापन केन्द्र',
    '🌊 ७७ जिल्ला — सबै official नदी स्टेशन': '🌊 ७७ जिल्ला — आधिकारिक नदी मापन केन्द्र',
    'Latest official reading; stale data लाई live खतरा मानिँदैन।': 'पछिल्लो आधिकारिक मापन मात्र देखाइन्छ; पुरानो मापनलाई प्रत्यक्ष खतरा मानिँदैन।',
    'Location, microphone र alert data कसरी प्रयोग हुन्छ हेर्नुहोस्।': 'स्थान, माइक्रोफोन र चेतावनीसम्बन्धी जानकारी कसरी प्रयोग हुन्छ हेर्नुहोस्।',
    '🇳🇵 FloodSafe Nepal-only monitoring\nतपाईं नेपाल बाहिर हुँदा नजिकको नदी चेतावनी पठाइँदैन। नेपालभित्र current GPS हुँदा २ km भित्रको प्रमाणित चेतावनी/खतरा मात्र आपतकालीन नदी चेतावनी आउँछ।': '🇳🇵 नेपाल बाहिर हुँदा नजिकको नदी चेतावनी निष्क्रिय हुन्छ।',
    '📍 पछिल्लो GPS • Nepal': '📍 पछिल्लो जीपीएस • नेपाल',
    '🌍 हालको GPS Nepal बाहिर • weather यही स्थानको हो': '🌍 हालको जीपीएस नेपाल बाहिर • मौसम यही स्थानको हो',
    '📍 हालको GPS • Nepal': '📍 हालको जीपीएस • नेपाल',
    '🌍 हालको GPS Nepal बाहिर • weather यही स्थानको हो': '🌍 हालको जीपीएस नेपाल बाहिर • मौसम यही स्थानको हो',
}
for old, new in repl.items():
    a = a.replace(old, new)

# Make all user-visible freshness wording match 20 minutes, targeted to the existing native UI.
a = a.replace('पछिल्लो ५ मिनेट', 'पछिल्लो २० मिनेट')
a = a.replace('५ मिनेटभित्र', '२० मिनेटभित्र')
a = a.replace('5 minutes', '20 minutes')
a = a.replace('within 5 min', 'within 20 min')
a = a.replace('within 5 minutes', 'within 20 minutes')

# Build identity.
if 'versionCode 74' in g:
    g = g.replace('versionCode 74', 'versionCode 76', 1)
elif 'versionCode 76' not in g:
    raise SystemExit('v0856 versionCode anchor missing')
if "versionName '0.8.54'" in g:
    g = g.replace("versionName '0.8.54'", "versionName '0.8.56'", 1)
elif "versionName '0.8.56'" not in g:
    raise SystemExit('v0856 versionName anchor missing')

for path, text in [(a_path,a),(w_path,w),(f_path,f),(t_path,t),(d_path,d),(s_path,s),(g_path,g)]:
    path.write_text(text, encoding='utf-8')

checks = {
    a_path: ['RIVER_FRESH_MS=20L*60L*1000L','V0856_NATIVE_TWENTY_MINUTE_FRESH','V0856_SAFE_LANGUAGE_RESTART','V0856_LANGUAGE_VISIBLE'],
    w_path: ['MAX_AGE_MS = 20L * 60L * 1000L','RADIUS_KM = 2d'],
    f_path: ['MAX_RIVER_AGE_MS = 20L * 60L * 1000L','DEFAULT_RIVER_RADIUS_KM = 2d'],
    t_path: ['FRESH_MS=20*60*1000','a<=FRESH_MS'],
    d_path: ['MAX_AGE=20*60*1000','freshWindowMinutes:20'],
    s_path: ['CURRENT_MS=20*60*1000','windowMinutes:20'],
    g_path: ['versionCode 76',"versionName '0.8.56'"],
}
for path, needles in checks.items():
    text=path.read_text(encoding='utf-8')
    for needle in needles:
        if needle not in text: raise SystemExit('v0856 verification failed: '+needle+' in '+str(path))

print('FloodSafe v0.8.56 PASS: crash-safe language switch + clean UI + 20-minute freshness; 2 km/map/weather unchanged')
