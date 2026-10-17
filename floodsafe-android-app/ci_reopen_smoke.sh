#!/usr/bin/env bash
set -euo pipefail

PKG='io.github.pujan1234hub.floodsafe.app'
APK='floodsafe-android-app/app/build/outputs/apk/debug/app-debug.apk'
LAUNCHER="$PKG/.PJBuiltsSplashActivity"
TARGET='NativeFullActivity'

test -s "$APK"
adb install -r "$APK"
adb shell pm grant "$PKG" android.permission.POST_NOTIFICATIONS || true
adb shell pm grant "$PKG" android.permission.ACCESS_COARSE_LOCATION || true
adb shell pm grant "$PKG" android.permission.ACCESS_FINE_LOCATION || true
adb shell input keyevent 82 || true
adb logcat -c

wait_target() {
  local label="$1"
  for _ in $(seq 1 35); do
    if adb shell dumpsys activity activities 2>/dev/null | grep -q "$TARGET"; then
      return 0
    fi
    sleep 1
  done
  echo "$TARGET did not become active: $label"
  adb shell dumpsys activity activities | tail -n 160 || true
  return 1
}

check_fatal() {
  adb logcat -d -v brief > /tmp/floodsafe-logcat.txt || true
  if grep -q "ANR in $PKG" /tmp/floodsafe-logcat.txt; then
    echo 'FloodSafe ANR detected'; return 1
  fi
  if grep -A14 'FATAL EXCEPTION' /tmp/floodsafe-logcat.txt | grep -q "$PKG"; then
    echo 'FloodSafe fatal exception detected';
    grep -A25 'FATAL EXCEPTION' /tmp/floodsafe-logcat.txt | tail -n 80 || true
    return 1
  fi
}

# Cold launch into the exact full-native screen used by the v0.9.18 UI.
adb shell am force-stop "$PKG"
adb shell am start -W -n "$LAUNCHER"
wait_target 'cold-1'
sleep 3
check_fatal

# Confirm the rendered native UI contains both the app and SATHI controls.
adb shell uiautomator dump /sdcard/floodsafe-window.xml >/dev/null 2>&1 || true
adb shell cat /sdcard/floodsafe-window.xml > /tmp/floodsafe-window.xml 2>/dev/null || true
grep -q 'FloodSafe Nepal' /tmp/floodsafe-window.xml
grep -q 'SATHI' /tmp/floodsafe-window.xml

# Warm reopen twice.
for label in warm-1 warm-2; do
  adb shell input keyevent KEYCODE_HOME
  sleep 2
  adb shell am start -W -n "$LAUNCHER"
  wait_target "$label"
  sleep 2
  check_fatal
done

# Force-stop and cold launch again to catch startup/provider crashes.
adb shell am force-stop "$PKG"
sleep 1
adb logcat -c
adb shell am start -W -n "$LAUNCHER"
wait_target 'cold-2'
sleep 4
check_fatal

echo 'FloodSafe NativeFullActivity cold/warm launcher + SATHI crash smoke PASS'
