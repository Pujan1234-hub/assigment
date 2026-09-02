package io.github.pujan1234hub.floodsafe.app;

import android.content.res.AssetManager;
import android.webkit.WebResourceResponse;
import androidx.webkit.WebViewAssetLoader;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.net.URLConnection;
import java.util.Collections;

final class BundledContent implements WebViewAssetLoader.PathHandler {
    private final AssetManager assets;
    BundledContent(AssetManager assets) { this.assets = assets; }

    @Override public WebResourceResponse handle(String path) {
        if (!NavigationPolicy.safeAssetPath(path)) return missing();
        try {
            String mime = URLConnection.guessContentTypeFromName(path);
            if (path.endsWith(".mjs") || path.endsWith(".js")) mime = "text/javascript";
            else if (path.endsWith(".json") || path.endsWith(".geojson")) mime = "application/json";
            else if (path.endsWith(".svg")) mime = "image/svg+xml";
            else if (path.endsWith(".css")) mime = "text/css";
            else if (path.endsWith(".wasm")) mime = "application/wasm";
            else if (path.endsWith(".woff2")) mime = "font/woff2";
            return new WebResourceResponse(mime == null ? "application/octet-stream" : mime,
                    "UTF-8", 200, "OK", Collections.singletonMap("Cache-Control", "no-store"),
                    assets.open(path));
        } catch (IOException absent) { return missing(); }
    }

    static WebResourceResponse missing() {
        return new WebResourceResponse("text/plain", "UTF-8", 404, "Not Found",
                Collections.emptyMap(), new ByteArrayInputStream(new byte[0]));
    }
}
