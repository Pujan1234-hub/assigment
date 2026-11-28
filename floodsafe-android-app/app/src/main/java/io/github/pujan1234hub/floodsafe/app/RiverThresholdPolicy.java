package io.github.pujan1234hub.floodsafe.app;

/** Never infer or swap conflicting official flood gauge limits. */
final class RiverThresholdPolicy {
    private RiverThresholdPolicy() {}
    static boolean conflicts(double warning, double danger) {
        return Double.isFinite(warning) && warning > 0d
            && Double.isFinite(danger) && danger > 0d && danger <= warning;
    }
}
