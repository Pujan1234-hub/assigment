from pathlib import Path

root = Path(__file__).resolve().parent
app = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path = app / 'NativeFullActivity.java'
g_path = root / 'app/build.gradle'

a = a_path.read_text(encoding='utf-8')
g = g_path.read_text(encoding='utf-8')

# v0.8.54 is intentionally narrow:
# 1) English mode renders English UI and Nepali mode renders Nepali UI.
# 2) Native river safety freshness is truly five minutes, matching v0.8.53
#    background/FCM/web safety paths. No map, colour, radius, weather or source logic changes.

# -----------------------------------------------------------------------------
# Language switching: rebuild the native view after changing the saved language.
# A number of labels are created once in buildScreen(); applyLanguage() alone cannot
# update those one-time controls. recreate() makes every t(ne,en) label use the new mode.
# -----------------------------------------------------------------------------
old = 'langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();applyLanguage();refreshRiverUi();});'
new = 'langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();recreate();}); // V0854_LANGUAGE_REBUILD'
if old in a:
    a = a.replace(old, new, 1)
elif 'V0854_LANGUAGE_REBUILD' not in a:
    raise SystemExit('v0854 language-toggle anchor missing')

# v0.8.50 separated source availability from safety freshness but hard-coded a
# 30-minute native freshness test. Tighten only that safety age to five minutes.
old = 'boolean fresh=hasObservation&&now-at<=30L*60L*1000L&&at-now<=5L*60L*1000L; // V0850_ONLINE_SEPARATE_FRESH'
new = 'boolean fresh=hasObservation&&now-at<=5L*60L*1000L&&at-now<=5L*60L*1000L; // V0854_NATIVE_FIVE_MINUTE_FRESH'
if old in a:
    a = a.replace(old, new, 1)
elif 'V0854_NATIVE_FIVE_MINUTE_FRESH' not in a:
    raise SystemExit('v0854 native five-minute freshness anchor missing')

# All river freshness wording produced by the v0.8.50/v0.8.51 native UI must
# describe the same five-minute rule. These are display strings only.
a = a.replace('३० मिनेट', '५ मिनेट')
a = a.replace('30 minutes', '5 minutes')
a = a.replace('30 min', '5 min')

# v0.8.52 added current-location UX after the language-cleanup pass. Clean only
# those later Nepali strings; English branches are left as proper English.
replacements = {
    't("Location बन्द छ","Location is off")': 't("स्थान सेवा बन्द छ","Location is off")',
    't("हालको स्थान देखाउन फोनको Location/GPS खोल्नुहोस्।","Turn on phone Location/GPS to show your current point on the map.")': 't("हालको स्थान देखाउन फोनको स्थान सेवा/जीपीएस खोल्नुहोस्।","Turn on phone Location/GPS to show your current point on the map.")',
    't("Location खोल्नुहोस्","Open location settings")': 't("स्थान सेवा खोल्नुहोस्","Open location settings")',
    't("Location भेटिएन — GPS on गरेर फेरि try गर्नुहोस्","Location not found — turn GPS on and try again")': 't("स्थान भेटिएन — जीपीएस खोलेर फेरि प्रयास गर्नुहोस्","Location not found — turn GPS on and try again")',
    't("🟢 उपलब्ध स्टेशन • ⚫ उपलब्ध छैन • 🔵 तपाईंको GPS","🟢 available station • ⚫ unavailable station • 🔵 your GPS")': 't("🟢 उपलब्ध मापन केन्द्र • ⚫ उपलब्ध छैन • 🔵 तपाईंको जीपीएस","🟢 available station • ⚫ unavailable station • 🔵 your GPS")',
    't("नेपालभित्रको GPS स्थान उपलब्ध भएपछि नजिकका केन्द्र बताउन सक्छु।","I can list nearby stations after a GPS location inside Nepal is available.")': 't("नेपालभित्रको जीपीएस स्थान उपलब्ध भएपछि नजिकका केन्द्र बताउन सक्छु।","I can list nearby stations after a GPS location inside Nepal is available.")',
    't("तपाईंको GPS नजिकका केन्द्र:","Stations nearest to your GPS:")': 't("तपाईंको जीपीएस नजिकका केन्द्र:","Stations nearest to your GPS:")',
}
for old_s, new_s in replacements.items():
    if old_s in a:
        a = a.replace(old_s, new_s)

# If any pre-v0.8.50 mixed Nepali wording survived later patches, normalize only
# the known UI phrases without changing data/source semantics.
cleanup = {
    'सबै official स्टेशन': 'सबै आधिकारिक मापन केन्द्र',
    'official नदी': 'आधिकारिक नदी',
    'official स्टेशन': 'आधिकारिक मापन केन्द्र',
    'official gauge': 'आधिकारिक मापन केन्द्र',
    'Official loss records मात्र': 'आधिकारिक क्षति अभिलेख मात्र',
    'Live news अहिले उपलब्ध छैन।': 'प्रत्यक्ष समाचार अहिले उपलब्ध छैन।',
    'नयाँ live समाचार भेटिएन।': 'नयाँ प्रत्यक्ष समाचार भेटिएन।',
    'मौसम data refresh हुँदैछ।': 'मौसमको तथ्याङ्क अद्यावधिक हुँदैछ।',
    'voice recognition उपलब्ध छैन।': 'आवाज पहिचान उपलब्ध छैन।',
    'warning वा app status': 'चेतावनी वा एपको अवस्था',
    'weather digest': 'मौसम सारांश',
    'verified Warning/Danger': 'प्रमाणित चेतावनी/खतरा',
    'emergency river alert': 'आपतकालीन नदी चेतावनी',
}
for old_s, new_s in cleanup.items():
    a = a.replace(old_s, new_s)

# The v0.8.50 clean-language pass intentionally keeps official acronyms such as
# BIPAD/DHM. Keep those proper names unchanged. Ensure language UI markers survive.
if 'V0850_LANGUAGE_CLEAN' not in a:
    raise SystemExit('v0854 expected v0850 language-clean base missing')
if 'RIVER_FRESH_MS=5L*60L*1000L' not in a:
    raise SystemExit('v0854 v0853 five-minute constant missing')
if 'V0854_NATIVE_FIVE_MINUTE_FRESH' not in a:
    raise SystemExit('v0854 native freshness marker missing')
if 'V0854_LANGUAGE_REBUILD' not in a:
    raise SystemExit('v0854 language rebuild marker missing')
if 'now-at<=30L*60L*1000L' in a:
    raise SystemExit('v0854 30-minute native safety freshness still present')

# New installable build identity. Runtime features are otherwise unchanged.
if 'versionCode 73' in g:
    g = g.replace('versionCode 73', 'versionCode 74', 1)
elif 'versionCode 74' not in g:
    raise SystemExit('v0854 versionCode anchor missing')
if "versionName '0.8.53'" in g:
    g = g.replace("versionName '0.8.53'", "versionName '0.8.54'", 1)
elif "versionName '0.8.54'" not in g:
    raise SystemExit('v0854 versionName anchor missing')

# Final consistency checks for the two requested fixes only.
for needle in [
    'versionCode 74',
    "versionName '0.8.54'",
]:
    if needle not in g:
        raise SystemExit('v0854 version verification failed: ' + needle)
for mixed in ['Location बन्द छ', 'GPS on गरेर फेरि try गर्नुहोस्']:
    if mixed in a:
        raise SystemExit('v0854 mixed Nepali phrase still present: ' + mixed)

a_path.write_text(a, encoding='utf-8')
g_path.write_text(g, encoding='utf-8')
print('FloodSafe v0.8.54 PASS: pure language switching + true 5-minute native freshness')
