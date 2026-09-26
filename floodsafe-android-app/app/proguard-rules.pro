# FloodSafe native debug/release shrinking rules.
# FloodSafeNativeMapView reads RiverStation fields reflectively, so keep this model intact.
-keep class io.github.pujan1234hub.floodsafe.app.NativeFullActivity$RiverStation { *; }

# Keep Firebase messaging service entry points declared through the manifest/service loader.
-keep class io.github.pujan1234hub.floodsafe.app.FloodSafeMessagingService { *; }
