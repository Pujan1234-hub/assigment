#!/usr/bin/env bash
set -euo pipefail

PKG='io.github.pujan1234hub.floodsafe.app'
TEST_PKG='io.github.pujan1234hub.floodsafe.app.test'
APK='floodsafe-android-app/app/build/outputs/apk/debug/app-debug.apk'
TEST_APK='floodsafe-android-app/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'
LAUNCHER="$PKG/.PJBuiltsSplashActivity"

# Build the instrumentation APK in the same shell so paths and status checks are reliable.
gradle -p floodsafe-android-app :app:assembleDebugAndroidTest -x bundleFloodSafe --no-daemon

test -s "$APK"
test -s "$TEST_APK"
adb install -r "$APK"
adb install -r "$TEST_APK"

adb shell pm grant "$PKG" android.permission.POST_NOTIFICATIONS || true
adb shell pm grant "$PKG" android.permission.ACCESS_COARSE_LOCATION || true
adb shell pm grant "$PKG" android.permission.ACCESS_FINE_LOCATION || true
adb shell pm grant "$PKG" android.permission.ACCESS_BACKGROUND_LOCATION || true
adb shell input keyevent 82 || true
adb logcat -c

wait_voice() {
  local label="$1"
  for _ in $(seq 1 30); do
    if adb shell dumpsys activity activities 2>/dev/null | grep -q 'VoiceMainActivity'; then
      return 0
    fi
    sleep 1
  done
  echo "VoiceMainActivity did not become active: $label"
  adb shell dumpsys activity activities | tail -n 140 || true
  return 1
}

# Actual launcher path: cold open -> Home -> reopen -> Home -> reopen -> force-stop -> cold open.
adb shell am force-stop "$PKG"
adb shell am start -W -n "$LAUNCHER"
wait_voice 'cold-1'

adb shell input keyevent KEYCODE_HOME
sleep 2
adb shell am start -W -n "$LAUNCHER"
wait_voice 'warm-1'

adb shell input keyevent KEYCODE_HOME
sleep 2
adb shell am start -W -n "$LAUNCHER"
wait_voice 'warm-2'

adb shell am force-stop "$PKG"
sleep 1
adb shell am start -W -n "$LAUNCHER"
wait_voice 'cold-2'

# WebView responsiveness regression test: checks document, map host and river runtime
# across cold/warm activity reopens, including JavaScript callback responsiveness.
set +e
adb shell am instrument -w \
  -e class io.github.pujan1234hub.floodsafe.app.ReopenSmokeTest \
  "$TEST_PKG/androidx.test.runner.AndroidJUnitRunner" | tee /tmp/reopen-test.txt
INSTRUMENT_STATUS=${PIPESTATUS[0]}
set -e

adb logcat -d -v brief > /tmp/floodsafe-logcat.txt || true

if [ "$INSTRUMENT_STATUS" -ne 0 ]; then
  echo "Instrumentation command failed: $INSTRUMENT_STATUS"
  exit 1
fi
if ! grep -Eq 'OK \(1 test\)' /tmp/reopen-test.txt; then
  echo 'Reopen regression test did not pass'
  cat /tmp/reopen-test.txt
  exit 1
fi
if grep -q "ANR in $PKG" /tmp/floodsafe-logcat.txt; then
  echo 'FloodSafe ANR detected'
  exit 1
fi
if grep -A10 'FATAL EXCEPTION' /tmp/floodsafe-logcat.txt | grep -q "$PKG"; then
  echo 'FloodSafe fatal exception detected'
  exit 1
fi

echo 'FloodSafe launcher cold/warm reopen + WebView responsiveness smoke PASS'
