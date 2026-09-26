#!/usr/bin/env bash
set -euo pipefail

APP=io.github.pujan1234hub.floodsafe.app
DIR=floodsafe-android-app
APK="$DIR/app/build/outputs/apk/debug/app-debug.apk"

echo '=== FloodSafe v0.9.02 runtime verification ==='
adb install -r "$APK"
adb shell pm grant "$APP" android.permission.POST_NOTIFICATIONS || true
adb shell pm grant "$APP" android.permission.ACCESS_FINE_LOCATION || true
adb shell pm grant "$APP" android.permission.ACCESS_COARSE_LOCATION || true
adb emu geo fix 85.3240 27.7172 || true
adb logcat -c
adb shell am start -W -n "$APP/.PJBuiltsSplashActivity"

# Official feeds + station-to-river mapping can take ~90 seconds on the CI emulator.
sleep 125
adb logcat -d > "$DIR/runtime-v0902-live.txt"

# Move from dashboard toward map / nearby stations.
adb shell input swipe 540 1950 540 520 700 || true
sleep 2
adb shell input swipe 540 1900 540 720 600 || true
sleep 4
adb exec-out screencap -p > "$DIR/runtime-v0902-map.png"

# Find a real station list row and open the native scrollable detail dialog.
ROW_FOUND=0
for N in 1 2 3 4 5 6 7 8; do
  adb shell uiautomator dump /sdcard/fs-ui.xml >/dev/null 2>&1 || true
  adb pull /sdcard/fs-ui.xml "$DIR/fs-ui.xml" >/dev/null 2>&1 || true
  if grep -q 'Current official reading\|Historical / last known reading' "$DIR/fs-ui.xml"; then ROW_FOUND=1; break; fi
  adb shell input swipe 540 1900 540 720 600 || true
  sleep 1
done
test "$ROW_FOUND" = 1
python3 - <<'PY' > /tmp/station-tap.txt
import re,xml.etree.ElementTree as ET
root=ET.parse('floodsafe-android-app/fs-ui.xml').getroot()
chosen=None
for e in root.iter():
    t=e.attrib.get('text','')
    if 'Current official reading' in t:
        chosen=e;break
    if chosen is None and 'Historical / last known reading' in t:
        chosen=e
assert chosen is not None, 'station row not found'
m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',chosen.attrib.get('bounds',''))
assert m, chosen.attrib
a,b,c,d=map(int,m.groups())
print((a+c)//2,(b+d)//2)
PY
read -r SX SY < /tmp/station-tap.txt
adb shell input tap "$SX" "$SY"
sleep 3
adb exec-out screencap -p > "$DIR/runtime-v0902-popup.png"
adb shell uiautomator dump /sdcard/fs-popup.xml >/dev/null 2>&1 || true
adb pull /sdcard/fs-popup.xml "$DIR/fs-popup.xml" >/dev/null 2>&1 || true
grep -q 'OK\|ठीक छ' "$DIR/fs-popup.xml"
adb shell input keyevent 4 || true
sleep 2

# Find and open native 77-district selector.
DIST_FOUND=0
for N in 1 2 3 4 5 6 7 8 9; do
  adb shell uiautomator dump /sdcard/fs-ui2.xml >/dev/null 2>&1 || true
  adb pull /sdcard/fs-ui2.xml "$DIR/fs-ui2.xml" >/dev/null 2>&1 || true
  if grep -q '७७ जिल्ला\|77 Districts' "$DIR/fs-ui2.xml"; then DIST_FOUND=1; break; fi
  adb shell input swipe 540 1900 540 720 600 || true
  sleep 1
done
test "$DIST_FOUND" = 1
python3 - <<'PY' > /tmp/district-button.txt
import re,xml.etree.ElementTree as ET
root=ET.parse('floodsafe-android-app/fs-ui2.xml').getroot()
for e in root.iter():
    t=e.attrib.get('text','')
    if '७७ जिल्ला' in t or '77 Districts' in t:
        m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',e.attrib.get('bounds',''))
        if m:
            a,b,c,d=map(int,m.groups());print((a+c)//2,(b+d)//2);break
PY
test -s /tmp/district-button.txt
read -r DX DY < /tmp/district-button.txt
adb shell input tap "$DX" "$DY"
sleep 2
adb exec-out screencap -p > "$DIR/runtime-v0902-district-selector.png"
adb shell uiautomator dump /sdcard/fs-district.xml >/dev/null 2>&1 || true
adb pull /sdcard/fs-district.xml "$DIR/fs-district.xml" >/dev/null 2>&1 || true
grep -q 'All Nepal\|सबै नेपाल' "$DIR/fs-district.xml"
grep -q 'Achham' "$DIR/fs-district.xml"
python3 - <<'PY' > /tmp/achham-tap.txt
import re,xml.etree.ElementTree as ET
root=ET.parse('floodsafe-android-app/fs-district.xml').getroot()
for e in root.iter():
    if e.attrib.get('text','').strip()=='Achham':
        m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',e.attrib.get('bounds',''))
        if m:
            a,b,c,d=map(int,m.groups());print((a+c)//2,(b+d)//2);break
PY
test -s /tmp/achham-tap.txt
read -r AX AY < /tmp/achham-tap.txt
adb shell input tap "$AX" "$AY"
sleep 3
adb exec-out screencap -p > "$DIR/runtime-v0902-district-selected.png"

adb logcat -d > "$DIR/runtime-v0902.txt"
grep -E 'FloodSafeTruth|FloodSafeStationColor|FloodSafeRiverColor|FloodSafeRiver|FloodSafeRain|FloodSafeDistrict|FloodSafeDialog' "$DIR/runtime-v0902.txt" | tail -360 || true

# Required runtime cases.
grep -Eq 'station_sources normal_green=[1-9][0-9]*' "$DIR/runtime-v0902.txt"
grep -Eq 'stale_grey=[1-9][0-9]*' "$DIR/runtime-v0902.txt"
grep -Eq 'flow_frame=[1-9][0-9]*.*normal_flow=[1-9][0-9]*' "$DIR/runtime-v0902.txt"
grep -q 'station-only river layers active' "$DIR/runtime-v0902.txt"
grep -Eq 'rain_match (ok|unavailable)' "$DIR/runtime-v0902.txt"
grep -q 'district_selector_count=77' "$DIR/runtime-v0902.txt"
grep -q 'map_focus_district=Achham' "$DIR/runtime-v0902.txt"
grep -Eq 'scroll_dialog_shown|river_scroll_dialog_shown' "$DIR/runtime-v0902.txt"

python3 - <<'PY'
import re
log=open('floodsafe-android-app/runtime-v0902.txt',errors='ignore').read()
truth=list(re.finditer(r'catalog=(\d+) merged=(\d+) bipad_rows_checked=(\d+) bipad_direct_current=(\d+) latest_readings=(\d+) current=(\d+)',log))
ui=list(re.finditer(r'ui current normal=(\d+) alert=(\d+) warning=(\d+) danger=(\d+) stale=(\d+)',log))
colors=list(re.finditer(r'river_status_features normal_cyan=(\d+) alert_yellow=(\d+) warning_orange=(\d+) danger_red=(\d+) stale_neutral=(\d+)',log))
assert truth and ui and colors, 'required truth/color runtime logs missing'
catalog,merged,checked,direct_current,latest,current=map(int,truth[-1].groups())
normal,alert,warning,danger,stale=map(int,ui[-1].groups())
rn,ra,rw,rd,rs=map(int,colors[-1].groups())
assert 250 <= catalog <= 320,(catalog,'catalog inventory unexpectedly changed')
assert merged <= catalog,(merged,catalog,'raw historical rows inflated inventory')
assert current > 0
assert normal+alert+warning+danger == current,(normal,alert,warning,danger,current)
assert normal+alert+warning+danger+stale == merged,(normal,alert,warning,danger,stale,merged)
if alert>0: assert ra>0,('current alert exists but no yellow matched river',alert,ra)
if warning>0: assert rw>0,('current warning exists but no orange matched river',warning,rw)
else: print('No current official warning in this runtime snapshot; orange test correctly conditional')
if danger>0: assert rd>0,('current danger exists but no red matched river',danger,rd)
else: print('No current official danger in this runtime snapshot; red test correctly conditional')
print('RUNTIME PARITY PASS',dict(catalog=catalog,valid_stations=merged,bipad_rows_checked=checked,bipad_direct_current=direct_current,latest=latest,current=current,normal=normal,alert=alert,warning=warning,danger=danger,stale=stale,normal_rivers=rn,alert_rivers=ra,warning_rivers=rw,danger_rivers=rd,stale_rivers=rs))
PY

echo '=== FloodSafe v0.9.02 runtime verification PASS ==='
