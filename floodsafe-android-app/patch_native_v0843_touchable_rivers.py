from pathlib import Path

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
g_path=root/'app/build.gradle'
m=m_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.43: keep the v0.8.42 progressive zoom tiers, but make rivers easier to see/tap.
# Do NOT bring back the v0.8.41 blue-wall effect. Only modestly increase the base core/glow,
# and enlarge the geographic tap tolerance so the finger does not need to land exactly on a thin line.

# Static geographic river style: clearer than v0.8.42, still much thinner than v0.8.41.
repls=[
    ('lineColor("#22D7FF"), lineWidth(1.25f), lineOpacity(0.92f)',
     'lineColor("#22D7FF"), lineWidth(1.80f), lineOpacity(0.96f)'),
    ('lineColor("#087CFF"), lineWidth(3.2f), lineOpacity(0.25f)',
     'lineColor("#087CFF"), lineWidth(4.6f), lineOpacity(0.30f)'),
    ('lineWidth((float)(2.9+0.7*wave))','lineWidth((float)(4.1+0.9*wave))'),
    ('lineWidth((float)(1.15+0.22*wave))','lineWidth((float)(1.65+0.30*wave))')]
for old,new in repls:
    if old not in m:
        raise SystemExit('v0.8.43 style anchor missing: '+old)
    m=m.replace(old,new,1)

# Finger-friendly tap radius. The renderer remains progressive; only hit selection becomes easier.
old='RiverWay rw=nearestRiver(p.getLatitude(),p.getLongitude(),Math.max(0.16,5.2/Math.pow(2.0,Math.max(0.0,zoom-6.0))));'
new='RiverWay rw=nearestRiver(p.getLatitude(),p.getLongitude(),Math.max(0.22,6.6/Math.pow(2.0,Math.max(0.0,zoom-6.0)))); // V0843_FINGER_FRIENDLY_RIVER_TAP'
if old not in m:
    raise SystemExit('v0.8.43 tap-radius anchor missing')
m=m.replace(old,new,1)

# Version bump only. Alerts/notifications/current-only truth remain untouched.
g=g.replace('versionCode 62','versionCode 63',1).replace("versionName '0.8.42'","versionName '0.8.43'",1)
if 'versionCode 63' not in g or "versionName '0.8.43'" not in g:
    raise SystemExit('v0.8.43 version bump failed')

for marker in [
    'V0842_PROGRESSIVE_ZOOM',
    'if(zoom<5.75)',
    'else if(zoom<6.65)',
    'if(zoom>=8.20)',
    'lineWidth(1.80f)',
    'lineWidth(4.6f)',
    'lineWidth((float)(4.1+0.9*wave))',
    'lineWidth((float)(1.65+0.30*wave))',
    'V0843_FINGER_FRIENDLY_RIVER_TAP']:
    if marker not in m:
        raise SystemExit('v0.8.43 marker missing: '+marker)

m_path.write_text(m,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.43 touchable rivers: medium-thin core/glow + larger tap target PASS')
