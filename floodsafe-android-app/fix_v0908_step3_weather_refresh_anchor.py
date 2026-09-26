from pathlib import Path

p = Path("floodsafe-android-app/patch_native_v0908_step3_storm_notifications.py")
s = p.read_text(encoding="utf-8")
old = '''refresh_count = ui.count('10L*60L*1000L')
if refresh_count != 2:
    raise SystemExit(f"foreground weather refresh expected 2 x 10min anchors, got {refresh_count}")
ui = ui.replace('10L*60L*1000L', '5L*60L*1000L')'''
new = '''weather_start_anchor = 'main.postDelayed(weatherRefreshTick,10L*60L*1000L)'
weather_repeat_anchor = 'main.postDelayed(this,10L*60L*1000L)'
start_count = ui.count(weather_start_anchor)
repeat_count = ui.count(weather_repeat_anchor)
if start_count != 1 or repeat_count != 1:
    raise SystemExit(f"foreground weather refresh anchors expected 1+1, got {start_count}+{repeat_count}")
ui = ui.replace(weather_start_anchor, 'main.postDelayed(weatherRefreshTick,5L*60L*1000L)', 1)
ui = ui.replace(weather_repeat_anchor, 'main.postDelayed(this,5L*60L*1000L)', 1)
# Keep the official river-freshness window unchanged. It is not a weather refresh timer.
if 'private static final long RIVER_FRESH_MS=10L*60L*1000L;' not in ui:
    raise SystemExit("river freshness guard changed unexpectedly")'''
if s.count(old) != 1:
    raise SystemExit(f"step3 refresh block expected once, got {s.count(old)}")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("V0908_STEP3_WEATHER_REFRESH_ANCHOR_FIXED")
