package io.github.pujan1234hub.floodsafe.app;

import java.net.URI;

final class NavigationPolicy {
    static final String HOST = "appassets.androidplatform.net";
    static final String ORIGIN = "https://" + HOST;
    static final String PATH = "/assets/floodsafe-nepal/v25/";
    static final String HOME = ORIGIN + PATH + "index.html";

    private NavigationPolicy() {}

    static boolean trustedOrigin(String value) {
        try {
            URI uri = URI.create(value);
            return "https".equals(uri.getScheme()) && HOST.equals(uri.getHost())
                    && uri.getUserInfo() == null && (uri.getPort() == -1 || uri.getPort() == 443);
        } catch (IllegalArgumentException | NullPointerException invalid) { return false; }
    }

    static boolean internalPage(String value) {
        if (!trustedOrigin(value)) return false;
        String path = URI.create(value).getPath();
        return PATH.equals(path) || (PATH + "index.html").equals(path);
    }

    static boolean externalHttps(String value) {
        try {
            URI uri = URI.create(value);
            return "https".equals(uri.getScheme()) && uri.getHost() != null
                    && uri.getUserInfo() == null && !HOST.equals(uri.getHost());
        } catch (IllegalArgumentException | NullPointerException invalid) { return false; }
    }

    static boolean safeAssetPath(String path) {
        if (path == null || path.isEmpty() || path.startsWith("/") || path.contains("\\")) return false;
        for (String part : path.split("/")) if (part.startsWith(".") || part.isEmpty()) return false;
        return path.startsWith("floodsafe-nepal/") || path.startsWith("data/");
    }
}
