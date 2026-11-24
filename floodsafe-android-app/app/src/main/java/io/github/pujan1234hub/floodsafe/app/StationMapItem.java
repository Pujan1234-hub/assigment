package io.github.pujan1234hub.floodsafe.app;

/**
 * Compile-time contract for all official river station markers.
 * Do not use getDeclaredField("lat"/"lon") here: R8 obfuscates private
 * activity models in Play release builds, leaving the map with zero pins.
 */
interface StationMapItem {
    String mapName();
    String mapStage();
    double mapLat();
    double mapLon();
    double mapLevel();
    double mapRainfallMm();
    boolean mapFresh();
}
