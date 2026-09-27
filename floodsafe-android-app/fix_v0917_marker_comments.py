from pathlib import Path
p=Path('floodsafe-android-app/patch_native_v0917_weather_runtime.py')
s=p.read_text(encoding='utf-8')
for token in ['V0917_NATIVE_WEATHER_PROXY','V0917_DISTRICT_WEATHER_PROXY','V0917_SATHI_WEATHER_PROXY','V0917_CURRENT_RAIN_PROXY']:
    old=f' // {token}'
    new=f' /* {token} */'
    if old not in s:
        raise SystemExit(f'marker missing: {token}')
    s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
print('V0917_MARKER_COMMENTS_FIXED')
