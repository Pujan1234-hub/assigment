package io.github.pujan1234hub.floodsafe.app;

import org.junit.Test;
import static org.junit.Assert.*;

public class RiverThresholdPolicyTest {
    @Test public void rejectsReportedMaiKholaReversal() {
        assertTrue(RiverThresholdPolicy.conflicts(5.50,4.30));
    }
    @Test public void rejectsEqualLimits() {
        assertTrue(RiverThresholdPolicy.conflicts(5.50,5.50));
    }
    @Test public void preservesOrderedLimits() {
        assertFalse(RiverThresholdPolicy.conflicts(4.30,5.50));
    }
    @Test public void missingLimitIsNotAnOrderedPair() {
        assertFalse(RiverThresholdPolicy.conflicts(Double.NaN,5.50));
        assertFalse(RiverThresholdPolicy.conflicts(4.30,Double.NaN));
        assertFalse(RiverThresholdPolicy.conflicts(0,5.50));
        assertFalse(RiverThresholdPolicy.conflicts(4.30,Double.POSITIVE_INFINITY));
    }
}
