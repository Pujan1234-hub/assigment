package io.github.pujan1234hub.floodsafe.app;

/** Pure safety policy for current-GPS river monitoring. */
final class MonitoringLocationPolicy {
    static final long MAX_FOLLOW_DEVICE_AGE_MS = 5L * 60L * 1000L;
    static final long FUTURE_TOLERANCE_MS = 2L * 60L * 1000L;

    private MonitoringLocationPolicy() {}

    static boolean shouldClearFollowDevice(boolean followDevice, long locationTime,
                                           long now, double lat, double lon) {
        if (!followDevice) return false;
        if (!Double.isFinite(lat) || !Double.isFinite(lon)) return true;
        if (!insideNepal(lat, lon)) return true;
        if (locationTime <= 0L) return true;
        long age = now - locationTime;
        return age > MAX_FOLLOW_DEVICE_AGE_MS || age < -FUTURE_TOLERANCE_MS;
    }

    static boolean insideNepal(double lat, double lon) {
        return Double.isFinite(lat) && Double.isFinite(lon)
                && lat >= 26.0d && lat <= 31.0d && lon >= 79.5d && lon <= 89.0d;
    }
}
