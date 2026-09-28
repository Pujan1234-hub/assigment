# FloodSafe native debug/release shrinking rules.
# FloodSafeNativeMapView reads RiverStation fields reflectively, so keep this model intact.
-keep class io.github.pujan1234hub.floodsafe.app.NativeFullActivity$RiverStation { *; }

# The v0.9.18 clean realtime hook calls the existing private refresh method and
# reads only the existing map/style fields. Preserve those member names through R8.
-keepclassmembers class io.github.pujan1234hub.floodsafe.app.NativeFullActivity {
    private void refreshRivers();
    private android.widget.TextView feedFresh;
    private io.github.pujan1234hub.floodsafe.app.FloodSafeNativeMapView map;
}
-keepclassmembers class io.github.pujan1234hub.floodsafe.app.FloodSafeNativeMapView {
    private org.maplibre.android.maps.Style style;
    private boolean styleReady;
}

# Keep Firebase messaging service entry points declared through the manifest/service loader.
-keep class io.github.pujan1234hub.floodsafe.app.FloodSafeMessagingService { *; }
