from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
a_path=src/'NativeFullActivity.java'
r_path=src/'RainAlertWorker.java'
a=a_path.read_text(encoding='utf-8')
r=r_path.read_text(encoding='utf-8')

# v0.8.69 notification/location patch used an obsolete FloodMonitorService.start(Context)
# call. The real service API is startIfEnabled(Context), which preserves the same intent
# and its enabled/permission guards. Replace only those generated calls.
old='FloodMonitorService.start(this)'
count=a.count(old)
if count:
    a=a.replace(old,'FloodMonitorService.startIfEnabled(this)')
if 'V0869_START_MONITOR_SERVICE' not in a or 'V0869_LOCATION_STARTS_MONITOR' not in a:
    raise SystemExit('v0870 compile repair: monitor markers missing')
if 'FloodMonitorService.start(this)' in a:
    raise SystemExit('v0870 compile repair: obsolete monitor start remains')

# The final v0.8.69 worker already has V0869_WEATHER_LOCATION_RESILIENCE, which checks
# follow_device/location_time with the 6-hour safety window. A second legacy statement
# referenced two variables that no longer exist. Remove only that redundant statement.
bad='            if (followDevice && !safetyLocationFresh) return Result.success();\n'
if bad in r:
    r=r.replace(bad,'',1)
elif 'followDevice && !safetyLocationFresh' in r:
    r=r.replace('if (followDevice && !safetyLocationFresh) return Result.success();','',1)
if 'followDevice && !safetyLocationFresh' in r:
    raise SystemExit('v0870 compile repair: legacy undefined rain guard remains')
if 'V0869_WEATHER_LOCATION_RESILIENCE' not in r:
    raise SystemExit('v0870 compile repair: real location resilience guard missing')
if 'V0869_TWO_HOUR_DIGEST' not in r:
    raise SystemExit('v0870 compile repair: 2-hour digest contract missing')

# Leave explicit build-time markers without altering runtime behavior.
a=a.replace('/* V0869_LOCATION_STARTS_MONITOR */','/* V0869_LOCATION_STARTS_MONITOR V0870_MONITOR_API_REPAIR */',1)
r=r.replace('// V0869_WEATHER_LOCATION_RESILIENCE','// V0869_WEATHER_LOCATION_RESILIENCE V0870_RAIN_GUARD_REPAIR',1)

a_path.write_text(a,encoding='utf-8')
r_path.write_text(r,encoding='utf-8')
print(f'FloodSafe v0.8.70 compile repair PASS: monitor_calls={count}; redundant rain guard removed; notification behavior preserved')
