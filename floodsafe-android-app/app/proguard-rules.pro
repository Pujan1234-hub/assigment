# FloodSafe native debug/release shrinking rules.
# FloodSafeNativeMapView reads RiverStation fields reflectively, so keep this model intact.
-keep class io.github.pujan1234hub.floodsafe.app.NativeFullActivity$RiverStation { *; }

# v0.9.18 realtime/visible-flow repair deliberately leaves the proven map classes
# byte-for-byte unchanged and reaches only these members reflectively. Keep their
# runtime names so R8/minification cannot silently disable the repair on-device.
-keepclassmembers class io.github.pujan1234hub.floodsafe.app.NativeFullActivity {
    private java.util.List stations;
    private io.github.pujan1234hub.floodsafe.app.FloodSafeNativeMapView map;
    private android.widget.TextView feedFresh;
    private android.widget.TextView nationalFresh;
    private void refreshRivers();
}
-keepclassmembers class io.github.pujan1234hub.floodsafe.app.FloodSafeNativeMapView {
    private org.maplibre.android.maps.Style style;
    private boolean styleReady;
    private java.util.List monitoredRivers;
}
-keep class io.github.pujan1234hub.floodsafe.app.FloodSafeNativeMapView$RiverWay { *; }

# Keep Firebase messaging service entry points declared through the manifest/service loader.
-keep class io.github.pujan1234hub.floodsafe.app.FloodSafeMessagingService { *; }
