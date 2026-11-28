package io.github.pujan1234hub.floodsafe.app;
import org.junit.Test;
import static org.junit.Assert.*;
public class RiverThresholdCatalogueTest {
 @Test public void knownPairFillsMissing(){RiverThresholdCatalogue.Match m=RiverThresholdCatalogue.merge(Double.NaN,Double.NaN,4.3,5.5);assertNotNull(m);assertEquals(4.3,m.warning,0);assertEquals(5.5,m.danger,0);}
 @Test public void rejectsContradictions(){assertNull(RiverThresholdCatalogue.merge(Double.NaN,Double.NaN,5.5,4.3));assertNull(RiverThresholdCatalogue.merge(4.0,Double.NaN,4.3,5.5));assertNull(RiverThresholdCatalogue.merge(4.3,Double.NaN,Double.NaN,5.5));}
 @Test public void confirmsSharedLimit(){assertNotNull(RiverThresholdCatalogue.merge(4.3,Double.NaN,4.3,5.5));}
 @Test public void matchesOnlySameGauge(){assertTrue(RiverThresholdCatalogue.sameGauge("MaiKhola at Chisapani","maikhola at chisapani",26.833324,87.89934,26.833324,87.89934));assertFalse(RiverThresholdCatalogue.sameGauge("MaiKhola at Chisapani","Karnali at Chisapani",26.833324,87.89934,26.833324,87.89934));assertFalse(RiverThresholdCatalogue.sameGauge("A","A",26.8,87.8,26.9,87.8));}
}
