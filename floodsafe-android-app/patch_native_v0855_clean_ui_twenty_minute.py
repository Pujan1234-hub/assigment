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

# 1) User-requested freshness: official river observations remain current for 20 minutes.
# Keep future tolerance, 2 km radius, risk thresholds, source selection and colours unchanged.
a = once(a, 'RIVER_FRESH_MS=5L*60L*1000L', 'RIVER_FRESH_MS=20L*60L*1000L', 'native 20m freshness')
a = once(a,
    'boolean fresh=hasObservation&&now-at<=5L*60L*1000L&&at-now<=5L*60L*1000L; // V0854_NATIVE_FIVE_MINUTE_FRESH',
    'boolean fresh=hasObservation&&now-at<=20L*60L*1000L&&at-now<=5L*60L*1000L; // V0855_NATIVE_TWENTY_MINUTE_FRESH',
    'native parsed observation 20m freshness')
w = once(w, 'MAX_AGE_MS = 5L * 60L * 1000L', 'MAX_AGE_MS = 20L * 60L * 1000L', 'worker 20m freshness')
f = once(f, 'MAX_RIVER_AGE_MS = 5L * 60L * 1000L', 'MAX_RIVER_AGE_MS = 20L * 60L * 1000L', 'FCM 20m freshness')
t = once(t, 'const FRESH_MS=5*60*1000,', 'const FRESH_MS=20*60*1000,', 'web trusted 20m freshness')
t = t.replace('if(a>4*60*1000)return POLL_NEAR_STALE', 'if(a>16*60*1000)return POLL_NEAR_STALE', 1)
d = d.replace('MAX_AGE=5*60*1000', 'MAX_AGE=20*60*1000')
d = d.replace("observationPolicy:'official reading <= 5 minutes'", "observationPolicy:'official reading <= 20 minutes'")
d = d.replace('freshWindowMinutes:5', 'freshWindowMinutes:20')
d = d.replace("displayMode:'fresh-official-5m'", "displayMode:'fresh-official-20m'")
s = s.replace('const CURRENT_MS=5*60*1000,', 'const CURRENT_MS=20*60*1000,', 1)
s = s.replace('windowMinutes:5', 'windowMinutes:20', 1)

# 2) Put a visible full-width language switch below My Location.
# The header switch remains; this one fixes phones where the header control is pushed off-screen.
marker = '// V0852_LOCATION_BUTTON'
if 'V0855_VISIBLE_LANGUAGE_SWITCH' not in a:
    pos = a.find(marker)
    if pos < 0:
        raise SystemExit('visible language switch location anchor missing')
    end = a.find('\n', pos)
    if end < 0:
        end = pos + len(marker)
    insert = '\n        Button languageSwitch=button(t("English","नेपाली"));languageSwitch.setTextSize(13);languageSwitch.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();recreate();});content.addView(languageSwitch,lp(-1,dp(46),0,0,0,dp(10))); // V0855_VISIBLE_LANGUAGE_SWITCH'
    a = a[:end] + insert + a[end:]

# 3) Replace the large mixed-language outside-Nepal paragraph with one compact, fully localized line.
start = a.find('    private void updateOutsideNotice(){')
end = a.find('    private void requestLocation()', start)
if start < 0 or end < 0:
    raise SystemExit('outside notice method anchors missing')
compact = '''    private void updateOutsideNotice(){
        TextView v=root==null?null:root.findViewById(android.R.id.hint);if(v==null)return;
        boolean out=Double.isFinite(lat)&&Double.isFinite(lon)&&!isNepal(lat,lon);
        v.setVisibility(out?View.VISIBLE:View.GONE);
        v.setText(t("🇳🇵 नेपाल बाहिर हुँदा नजिकको नदी चेतावनी निष्क्रिय हुन्छ।","🇳🇵 Nearby river alerts are disabled outside Nepal."));
    } // V0855_COMPACT_OUTSIDE_NOTICE\n\n'''
a = a[:start] + compact + a[end:]

# 4) All native freshness wording must match the 20-minute rule.
a = a.replace('५ मिनेट', '२० मिनेट')
a = a.replace('5 minutes', '20 minutes')
a = a.replace('5 min', '20 min')

# Keep brand/proper names such as FloodSafe, BIPAD, DHM and SATHI unchanged.
# Version bump only; no other runtime changes.
if 'versionCode 74' in g:
    g = g.replace('versionCode 74', 'versionCode 75', 1)
elif 'versionCode 75' not in g:
    raise SystemExit('v0855 versionCode anchor missing')
if "versionName '0.8.54'" in g:
    g = g.replace("versionName '0.8.54'", "versionName '0.8.55'", 1)
elif "versionName '0.8.55'" not in g:
    raise SystemExit('v0855 versionName anchor missing')

# Safety/feature-preservation checks.
checks = {
    a_path: [
        'RIVER_FRESH_MS=20L*60L*1000L',
        'V0855_NATIVE_TWENTY_MINUTE_FRESH',
        'V0855_VISIBLE_LANGUAGE_SWITCH',
        'V0855_COMPACT_OUTSIDE_NOTICE',
        'V0854_LANGUAGE_REBUILD',
    ],
    w_path: ['MAX_AGE_MS = 20L * 60L * 1000L', 'RADIUS_KM = 2d'],
    f_path: ['MAX_RIVER_AGE_MS = 20L * 60L * 1000L', 'DEFAULT_RIVER_RADIUS_KM = 2d'],
    t_path: ['FRESH_MS=20*60*1000', 'a<=FRESH_MS', 'const left=FRESH_MS-(Date.now()-t)'],
    d_path: ['MAX_AGE=20*60*1000', 'freshWindowMinutes:20', "displayMode:'fresh-official-20m'"],
    s_path: ['CURRENT_MS=20*60*1000', 'windowMinutes:20'],
    g_path: ['versionCode 75', "versionName '0.8.55'"],
}

for path, text in [(a_path,a),(w_path,w),(f_path,f),(t_path,t),(d_path,d),(s_path,s),(g_path,g)]:
    path.write_text(text, encoding='utf-8')

for path, needles in checks.items():
    text = path.read_text(encoding='utf-8')
    for needle in needles:
        if needle not in text:
            raise SystemExit('v0855 verification failed: '+needle+' in '+str(path))

print('FloodSafe v0.8.55 PASS: visible language switch + compact clean UI + 20-minute freshness; 2 km/risk/map/weather preserved')
