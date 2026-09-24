from pathlib import Path

ROOT = Path(__file__).resolve().parent
JAVA = ROOT / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'

native = JAVA / 'NativeFullActivity.java'
voice = JAVA / 'VoiceMainActivity.java'
gradle = ROOT / 'app/build.gradle'

text = native.read_text(encoding='utf-8')

# Make the existing full native screen reusable as the launcher/notification target.
text = text.replace(
    'public final class NativeFullActivity extends Activity implements LocationListener {',
    'public class NativeFullActivity extends Activity implements LocationListener {',
    1,
)

# Do not mix river-source labels. River/station status is BIPAD in the native UI.
text = text.replace(
    'नेपालको मौसम + official BIPAD/DHM realtime नदी status',
    'नेपालको मौसम + official BIPAD realtime नदी status',
)
text = text.replace(
    'Local weather + official BIPAD/DHM river status',
    'Local weather + official BIPAD river status',
)
text = text.replace('Source: BIPAD / DHM', 'Source: BIPAD official')

# FloodSafe status palette: danger red, warning orange, alert yellow,
# normal blue, stale/unknown grey.
text = text.replace(
    'case"normal":return Color.rgb(31,164,116);default:return Color.rgb(113,139,155);',
    'case"normal":return Color.rgb(31,132,219);default:return Color.rgb(113,139,155);',
)
text = text.replace(
    'case"normal":return Color.rgb(233,255,245);default:return Color.rgb(243,249,252);',
    'case"normal":return Color.rgb(235,246,255);default:return Color.rgb(243,249,252);',
)
text = text.replace('case"normal":return"🟢";', 'case"normal":return"🔵";')

# Native live refresh: avoid concurrent network fetches and refresh visible river
# readings every 10 seconds while the activity is alive.
field = '    private boolean showAllStations=false;\n'
if 'riverRefreshInFlight' not in text:
    text = text.replace(
        field,
        field + '    private boolean riverRefreshInFlight=false;\n'
        '    private final Runnable riverPoll=new Runnable(){@Override public void run(){refreshRivers();main.postDelayed(this,10000L);}};\n',
        1,
    )

if 'main.postDelayed(riverPoll,10000L);' not in text:
    text = text.replace(
        '        refreshAll();\n        requestLocation();',
        '        refreshAll();\n        main.postDelayed(riverPoll,10000L);\n        requestLocation();',
        1,
    )

old_start = '    private void refreshRivers(){feedFresh.setText('
new_start = '    private void refreshRivers(){if(riverRefreshInFlight)return;riverRefreshInFlight=true;feedFresh.setText('
if old_start in text:
    text = text.replace(old_start, new_start, 1)

text = text.replace(
    'runOnUiThread(this::refreshRiverUi);}catch(Exception e){runOnUiThread(()->feedFresh.setText(',
    'runOnUiThread(()->{riverRefreshInFlight=false;refreshRiverUi();});}catch(Exception e){runOnUiThread(()->{riverRefreshInFlight=false;feedFresh.setText(',
    1,
)
text = text.replace(
    '"River refresh failed • stale data is not live")));}});}',
    '"River refresh failed • stale data is not live"));});}});}',
    1,
)

# Assertions so CI fails rather than silently producing a WebView launcher.
required = [
    'public class NativeFullActivity extends Activity implements LocationListener',
    'private final Runnable riverPoll=',
    'Source: BIPAD official',
    'case"normal":return"🔵";',
]
for marker in required:
    if marker not in text:
        raise SystemExit(f'Native patch marker missing: {marker}')
if 'import android.webkit.WebView' in text:
    raise SystemExit('NativeFullActivity must not import WebView')

native.write_text(text, encoding='utf-8')

# All legacy intents (launcher, SATHI wake, FCM notification) already target
# VoiceMainActivity. Turn it into a tiny native alias so every path lands in the
# same native Activity and none of those paths can open the old WebView shell.
voice.write_text('''package io.github.pujan1234hub.floodsafe.app;\n\n/** Native launcher alias. No WebView is used. */\npublic final class VoiceMainActivity extends NativeFullActivity {\n}\n''', encoding='utf-8')

# Give the native artifact its own version identity.
g = gradle.read_text(encoding='utf-8')
g = g.replace('versionCode 14', 'versionCode 15', 1)
g = g.replace("versionName '0.7.0'", "versionName '0.8.0'", 1)
if 'versionCode 15' not in g or "versionName '0.8.0'" not in g:
    raise SystemExit('Native version bump failed')
gradle.write_text(g, encoding='utf-8')

print('FloodSafe full native patch PASS: launcher + SATHI + push -> native Activity; no WebView path')
