from pathlib import Path

p = Path('floodsafe-android-app/patch_native_v0915_weather_icons.py')
s = p.read_text(encoding='utf-8')
old = '''s = repl(
    s,
    '        setGeo(style, SRC_DHM_RAIN_HEAVY, EMPTY);',
    '        setGeo(style, SRC_DHM_RAIN_HEAVY, EMPTY);\\n'
    '        setGeo(style, SRC_ICON_CLEAR, EMPTY);\\n'
    '        setGeo(style, SRC_ICON_CLOUD, EMPTY);\\n'
    '        setGeo(style, SRC_ICON_RAIN, EMPTY);\\n'
    '        setGeo(style, SRC_ICON_THUNDER, EMPTY);',
    'clear weather icons',
)
'''
new = '''old_clear = '        setGeo(style, SRC_DHM_RAIN_HEAVY, EMPTY);'
new_clear = ('        setGeo(style, SRC_DHM_RAIN_HEAVY, EMPTY);\\n'
             '        setGeo(style, SRC_ICON_CLEAR, EMPTY);\\n'
             '        setGeo(style, SRC_ICON_CLOUD, EMPTY);\\n'
             '        setGeo(style, SRC_ICON_RAIN, EMPTY);\\n'
             '        setGeo(style, SRC_ICON_THUNDER, EMPTY);')
if old_clear not in s:
    raise SystemExit('clear weather icon anchor missing')
s = s.replace(old_clear, new_clear, 1)
'''
if old not in s:
    raise SystemExit('v0915 clear block not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('V0915_PATCH_SCRIPT_CLEAR_ANCHOR_FIXED')
