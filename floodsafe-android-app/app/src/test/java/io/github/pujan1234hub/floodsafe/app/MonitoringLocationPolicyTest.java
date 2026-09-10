package io.github.pujan1234hub.floodsafe.app;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import org.junit.Test;

public final class MonitoringLocationPolicyTest {
    private static final long NOW = 1_800_000_000_000L;

    @Test public void freshNepalCurrentGpsIsAccepted() {
        assertFalse(MonitoringLocationPolicy.shouldClearFollowDevice(
                true, NOW - 60_000L, NOW, 27.7172d, 85.3240d));
    }

    @Test public void staleCurrentGpsIsRejected() {
        assertTrue(MonitoringLocationPolicy.shouldClearFollowDevice(
                true, NOW - 6L * 60L * 1000L, NOW, 27.7172d, 85.3240d));
    }

    @Test public void outsideNepalCurrentGpsIsRejectedImmediately() {
        assertTrue(MonitoringLocationPolicy.shouldClearFollowDevice(
                true, NOW - 30_000L, NOW, 50.7184d, -3.5339d));
    }

    @Test public void badFutureTimestampIsRejected() {
        assertTrue(MonitoringLocationPolicy.shouldClearFollowDevice(
                true, NOW + 3L * 60L * 1000L, NOW, 27.7172d, 85.3240d));
    }

    @Test public void manualMonitoringPointIsNotClearedByCurrentGpsGuard() {
        assertFalse(MonitoringLocationPolicy.shouldClearFollowDevice(
                false, 0L, NOW, 27.7172d, 85.3240d));
    }
}
