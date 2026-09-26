from pathlib import Path
import re

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
g_path=root/'app/build.gradle'
main_path=src/'MainActivity.java'
voice_path=src/'VoiceMainActivity.java'
splash_path=src/'PJBuiltsSplashActivity.java'
bundled_path=src/'BundledContent.java'

g=g_path.read_text(encoding='utf-8')

# Replace the old WebView asset bundler with a native-data-only bundle. Keep the
# task name because the river preprocessing pipeline already invokes bundleFloodSafe.
start=g.find("def bundleWeb = tasks.register('bundleFloodSafe', Copy) {")
end_anchor="tasks.named('preBuild').configure { dependsOn bundleWeb }"
end=g.find(end_anchor)
if start<0 or end<0: raise SystemExit('v0897d old bundleFloodSafe block missing')
end += len(end_anchor)
new_block=r'''def bundleNativeData = tasks.register('bundleFloodSafe', Copy) {
    doFirst { delete generatedFloodSafeAssets.get().asFile }
    from(rootProject.file('../data')) {
        into 'data'
        exclude 'floodsafe-people-status.json'
    }
    // Native MapLibre district boundary only. No HTML/JS application bundle.
    from(rootProject.file('../floodsafe-nepal/v24')) {
        include 'nepal-districts.geojson'
        include 'nepal-districts.json'
        into 'floodsafe-nepal/v24'
    }
    includeEmptyDirs = false
    into(generatedFloodSafeAssets)
    doLast {
        def core = new File(generatedFloodSafeAssets.get().asFile, 'data/floodsafe-core.json')
        def waterways = new File(generatedFloodSafeAssets.get().asFile, 'data/nepal-waterways-snapshot.json')
        def districts = new File(generatedFloodSafeAssets.get().asFile, 'floodsafe-nepal/v24/nepal-districts.geojson')
        if (!core.isFile() || !waterways.isFile() || !districts.isFile()) {
            throw new GradleException('Native FloodSafe data assets missing')
        }
        def forbidden = fileTree(generatedFloodSafeAssets.get().asFile) {
            include '**/*.html', '**/*.htm', '**/*.js', '**/*.mjs', '**/*.webmanifest'
        }.files
        if (!forbidden.isEmpty()) throw new GradleException('Web assets leaked into native-only package: ' + forbidden)
        println 'FloodSafe native-only asset bundle PASS: data + MapLibre geometry only'
    }
}
tasks.named('preBuild').configure { dependsOn bundleNativeData }'''
g=g[:start]+new_block+g[end:]

g=g.replace("    implementation 'androidx.webkit:webkit:1.12.1'\n",'')
g=re.sub(r'versionCode\s+117\b','versionCode 118',g,count=1)
g=g.replace("versionName '0.8.97'","versionName '0.8.97-native'",1)
if "versionName '0.8.97-native'" not in g: raise SystemExit('v0897d version bump failed')
g_path.write_text(g,encoding='utf-8')

redirect='''package io.github.pujan1234hub.floodsafe.app;\n\nimport android.app.Activity;\nimport android.content.Intent;\nimport android.os.Bundle;\n\n/** Native-only compatibility entry point. */\npublic class MainActivity extends Activity {\n    @Override public void onCreate(Bundle state) {\n        super.onCreate(state);\n        Intent i=new Intent(this, NativeFullActivity.class);\n        if(getIntent()!=null){ i.setData(getIntent().getData()); if(getIntent().getExtras()!=null)i.putExtras(getIntent().getExtras()); }\n        startActivity(i);\n        finish();\n    }\n}\n'''
main_path.write_text(redirect,encoding='utf-8')
voice='''package io.github.pujan1234hub.floodsafe.app;\n\nimport android.app.Activity;\nimport android.content.Intent;\nimport android.os.Bundle;\n\n/** Native-only compatibility entry point for older SATHI intents. */\npublic final class VoiceMainActivity extends Activity {\n    @Override public void onCreate(Bundle state) {\n        super.onCreate(state);\n        Intent i=new Intent(this, NativeFullActivity.class);\n        if(getIntent()!=null){ i.setData(getIntent().getData()); if(getIntent().getExtras()!=null)i.putExtras(getIntent().getExtras()); }\n        startActivity(i);\n        finish();\n    }\n}\n'''
voice_path.write_text(voice,encoding='utf-8')

if bundled_path.exists(): bundled_path.unlink()

s=splash_path.read_text(encoding='utf-8')
s=s.replace('new Intent(this, VoiceMainActivity.class)','new Intent(this, NativeFullActivity.class)')
s=s.replace('// Do NOT clear the task here. Clearing it destroyed the already-loaded WebView\n        // on every launcher reopen, forcing a full cold reload of map, river, news and\n        // SATHI. CLEAR_TOP + SINGLE_TOP reuses the existing VoiceMainActivity when it\n        // is alive, while still creating it normally on a genuine cold start.\n','// Reuse the native activity on launcher reopen.\n')
splash_path.write_text(s,encoding='utf-8')

# Reject actual WebKit imports/references, but do not fail on documentation comments
# such as "No WebView is used" in native classes.
left=[]
for p in src.glob('*.java'):
    t=p.read_text(encoding='utf-8')
    if 'android.webkit' in t or 'androidx.webkit' in t or re.search(r'\bnew\s+WebView\s*\(',t):
        left.append(p.name)
if left: raise SystemExit('v0897d actual WebKit source remained: '+','.join(left))

print('v0.8.97d native-only packaging + entry-point cleanup applied')
