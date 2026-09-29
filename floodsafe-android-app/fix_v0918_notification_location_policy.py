from pathlib import Path

J = Path('floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app')
policy = J / 'MonitoringLocationPolicy.java'
s = policy.read_text(encoding='utf-8')

# Preserve the original 5-minute safety contract used by river/FCM/current-device checks.
s = s.replace(
    'static final long MAX_FOLLOW_DEVICE_AGE_MS = 2L * 60L * 60L * 1000L; // V0918_LOCK_WEATHER_LOCATION_WINDOW\n'
    '    static final long MAX_RIVER_DEVICE_AGE_MS = 30L * 60L * 1000L; // V0918_LOCK_RIVER_LOCATION_WINDOW',
    'static final long MAX_FOLLOW_DEVICE_AGE_MS = 5L * 60L * 1000L; // original safety window preserved\n'
    '    static final long MAX_WEATHER_LOCK_AGE_MS = 2L * 60L * 60L * 1000L; // V0918_LOCK_WEATHER_LOCATION_WINDOW\n'
    '    // V0918_LOCK_RIVER_LOCATION_WINDOW: river/FCM continues to use original 5-minute freshDeviceLocation policy',
    1,
)

old = '''    static boolean freshNepalDeviceLocation(long locationTime, long now, double lat, double lon) {
        if (!insideNepal(lat, lon) || locationTime <= 0L) return false;
        long age = now - locationTime;
        return age <= MAX_RIVER_DEVICE_AGE_MS && age >= -FUTURE_TOLERANCE_MS;
    }'''
new = '''    static boolean freshNepalDeviceLocation(long locationTime, long now, double lat, double lon) {
        return freshDeviceLocation(locationTime, now, lat, lon) && insideNepal(lat, lon);
    }

    static boolean freshWeatherLockLocation(long locationTime, long now, double lat, double lon) {
        if (!Double.isFinite(lat) || !Double.isFinite(lon)) return false;
        if (lat < -90d || lat > 90d || lon < -180d || lon > 180d) return false;
        if (locationTime <= 0L) return false;
        long age = now - locationTime;
        return age <= MAX_WEATHER_LOCK_AGE_MS && age >= -FUTURE_TOLERANCE_MS;
    }'''
if old in s:
    s = s.replace(old, new, 1)
if 'MAX_WEATHER_LOCK_AGE_MS' not in s or 'freshWeatherLockLocation' not in s:
    raise SystemExit('weather lock location policy repair failed')
policy.write_text(s, encoding='utf-8')

locked = J / 'LockedNotificationMonitor.java'
l = locked.read_text(encoding='utf-8')
l = l.replace('MonitoringLocationPolicy.freshDeviceLocation(locationAt,nowMs,lat,lon)',
              'MonitoringLocationPolicy.freshWeatherLockLocation(locationAt,nowMs,lat,lon)', 1)
if 'freshWeatherLockLocation' not in l:
    raise SystemExit('locked notifier weather location call repair failed')
locked.write_text(l, encoding='utf-8')

print('V0918_NOTIFICATION_LOCATION_POLICY_SAFE')
