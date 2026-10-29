package io.github.pujan1234hub.floodsafe.app;
import java.net.URI;
/** Only the current PJBUILTS FloodSafe Nepal live site can navigate inside the native shell. */
final class NavigationPolicy {
    static final String HOST = "appassets.androidplatform.net";
    static final String ORIGIN = "https://" + HOST;
    static final String PATH = "/assets/floodsafe-nepal/v25/";
    static final String HOME = ORIGIN + PATH + "index.html"; // legacy bundled tests / fallback
    static final String LIVE_HOST = "pjbuilts.com";
    static final String LIVE_PATH = "/floodsafe-nepal/";
    static final String LIVE_HOME = "https://pjbuilts.com/floodsafe-nepal/";
    private NavigationPolicy() {}
    private static URI parse(String value) {
        try {
            URI u=URI.create(value);
            if(!"https".equalsIgnoreCase(u.getScheme()) || u.getUserInfo()!=null
                    || (u.getPort()!=-1 && u.getPort()!=443))return null;
            return u;
        }catch(Exception ignored){return null;}
    }
    static boolean assetOrigin(String value) {
        URI u=parse(value);
        return u!=null&&HOST.equalsIgnoreCase(u.getHost());
    }
    static boolean liveOrigin(String value) {
        URI u=parse(value);
        return u!=null&&LIVE_HOST.equalsIgnoreCase(u.getHost());
    }
    static boolean trustedOrigin(String value) {return assetOrigin(value)||liveOrigin(value);}
    static boolean internalPage(String value) {
        URI u=parse(value);if(u==null)return false;
        String path=u.getPath();
        if(HOST.equalsIgnoreCase(u.getHost()))return PATH.equals(path)
           ||(PATH+"index.html").equals(path)||(PATH+"privacy.html").equals(path);
        if(LIVE_HOST.equalsIgnoreCase(u.getHost()))return path!=null
           && ("/floodsafe-nepal".equals(path)||path.startsWith(LIVE_PATH));
        return false;
    }
    static boolean externalHttps(String value) {
        URI u=parse(value);
        return u!=null&&u.getHost()!=null&&!assetOrigin(value)&&!internalPage(value);
    }
    static boolean safeAssetPath(String path) {
        if(path==null||path.isEmpty()||path.startsWith("/")||path.contains("\\"))return false;
        for(String part:path.split("/"))if(part.startsWith(".")||part.isEmpty())return false;
        return path.startsWith("floodsafe-nepal/")||path.startsWith("data/");
    }
}
